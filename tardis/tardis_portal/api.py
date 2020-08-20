# pylint: disable=C0302
'''
RESTful API for MyTardis models and data.
Implemented with Tastypie.
.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json
import re
from wsgiref.util import FileWrapper

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseForbidden, \
    StreamingHttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import redirect

from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authentication import SessionAuthentication
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.exceptions import NotFound
from tastypie.exceptions import Unauthorized
from tastypie.http import HttpUnauthorized
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField

from uritemplate import URITemplate

from tardis.analytics.tracker import IteratorTracker
from . import tasks
from .auth.decorators import (
    get_accessible_datafiles_for_user,
    has_access,
    has_download_access,
    has_write,
    has_delete_permissions,
    has_sensitive_access
)
from .auth.localdb_auth import django_user, django_group
from .models.access_control import ObjectACL, UserProfile, UserAuthentication, GroupAdmin
from .models.datafile import DataFile, DataFileObject, compute_checksums
from .models.dataset import Dataset
from .models.experiment import Experiment, ExperimentAuthor
from .models.project import Project
from .models.parameters import (
    DatafileParameter,
    DatafileParameterSet,
    DatasetParameter,
    DatasetParameterSet,
    ExperimentParameter,
    ExperimentParameterSet,
    ParameterName,
    ProjectParameter,
    ProjectParameterSet,
    Schema)
from .models.storage import StorageBox, StorageBoxOption, StorageBoxAttribute
from .models.facility import Facility, facilities_managed_by
from .models.instrument import Instrument
from .models.institution import Institution

import ldap3
import logging

logger = logging.getLogger('__name__')

add_group_perm = Permission.objects.get(codename='add_group')
change_group_perm = Permission.objects.get(codename='change_group')
del_group_perm = Permission.objects.get(codename='delete_group')
view_group_perm = Permission.objects.get(codename='view_group')
add_project_perm = Permission.objects.get(codename='add_project')
change_project_perm = Permission.objects.get(codename='change_project')
del_project_perm = Permission.objects.get(codename='delete_project')
view_project_perm = Permission.objects.get(codename='view_project')
add_experiment_perm = Permission.objects.get(codename='add_experiment')
change_experiment_perm = Permission.objects.get(codename='change_experiment')
del_experiment_perm = Permission.objects.get(codename='delete_experiment')
view_experiment_perm = Permission.objects.get(codename='view_experiment')
add_dataset_perm = Permission.objects.get(codename='add_dataset')
change_dataset_perm = Permission.objects.get(codename='change_dataset')
del_dataset_perm = Permission.objects.get(codename='delete_dataset')
view_dataset_perm = Permission.objects.get(codename='view_dataset')
add_datafile_perm = Permission.objects.get(codename='add_datafile')
change_datafile_perm = Permission.objects.get(codename='change_datafile')
del_datafile_perm = Permission.objects.get(codename='delete_datafile')
view_datafile_perm = Permission.objects.get(codename='view_datafile')

admin_perms = [add_group_perm,
               change_group_perm,
               del_group_perm,
               view_group_perm,
               add_project_perm,
               change_project_perm,
               del_project_perm,
               view_project_perm,
               add_experiment_perm,
               change_experiment_perm,
               del_experiment_perm,
               view_experiment_perm,
               add_dataset_perm,
               change_dataset_perm,
               del_dataset_perm,
               view_dataset_perm,
               add_datafile_perm,
               change_datafile_perm,
               del_datafile_perm,
               view_datafile_perm]

member_perms = [view_project_perm,
                view_experiment_perm,
                view_dataset_perm,
                view_datafile_perm]


def get_user_from_upi(upi):
    server = ldap3.Server(settings.LDAP_URL)
    search_filter = "({}={})".format(settings.LDAP_USER_LOGIN_ATTR, upi)
    with ldap3.Connection(server,
                          auto_bind=True,
                          user=settings.LDAP_ADMIN_USER,
                          password=settings.LDAP_ADMIN_PASSWORD) as connection:
        connection.search(settings.LDAP_USER_BASE,
                          search_filter,
                          attributes=['*'])
        if len(connection.entries) > 1:
            error_message = "More than one person with {}: {} has been found in the LDAP".format(settings.LDAP_USER_LOGIN_ATTR, upi)
            if logger:
                logger.error(error_message)
            raise Exception(error_message)
        elif len(connection.entries) == 0:
            error_message = "No one with {}: {} has been found in the LDAP".format(settings.LDAP_USER_LOGIN_ATTR, upi)
            if logger:
                logger.warning(error_message)
            return None
        else:
            person = connection.entries[0]
            first_name_key = 'givenName'
            last_name_key = 'sn'
            email_key = 'mail'
            username = person[settings.LDAP_USER_LOGIN_ATTR].value
            first_name = person[first_name_key].value
            last_name = person[last_name_key].value
            try:
                email = person[email_key].value
            except KeyError:
                email = ''
            details = {'username': username,
                       'first_name': first_name,
                       'last_name': last_name,
                       'email': email}
            logger.error(details)
            return details


def gen_random_password():
    import random
    random.seed()
    characters = 'abcdefghijklmnopqrstuvwxyzABCDFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?'
    passlen = 16
    password = "".join(random.sample(characters, passlen))
    return password


def create_acl(content_type,
               object_id,
               plugin_id,
               entity_id,
               write=False,
               download=False,
               sensitive=False,
               owner=False,
               admin=False):
    if admin:
        download = True
        sensitive = True
        owner = True
        write = True
    acl = ObjectACL(content_type=content_type,
                    object_id=object_id,
                    pluginId=plugin_id,
                    entityId=str(entity_id),
                    canRead=True,
                    canDownload=download,
                    canWrite=write,
                    canDelete=False,
                    canSensitive=sensitive,
                    isOwner=owner,
                    aclOwnershipType=ObjectACL.OWNER_OWNED)
    acl.save()
    return True


class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data, cls=json.JSONEncoder,
                          sort_keys=True, ensure_ascii=False,
                          indent=self.json_indent) + "\n"


if settings.DEBUG:
    default_serializer = PrettyJSONSerializer()
else:
    default_serializer = Serializer()


class MyTardisAuthentication(object):
    '''
    custom tastypie authentication that works with both anonymous use and
    a number of available auth mechanisms.
    '''

    def is_authenticated(self, request, **kwargs):  # noqa # too complex
        '''
        handles backends explicitly so that it can return False when
        credentials are given but wrong and return Anonymous User when
        credentials are not given or the session has expired (web use).
        '''
        auth_info = request.META.get('HTTP_AUTHORIZATION')

        if 'HTTP_AUTHORIZATION' not in request.META:
            if hasattr(request.user, 'allowed_tokens'):
                tokens = request.user.allowed_tokens
            session_auth = SessionAuthentication()
            check = session_auth.is_authenticated(request, **kwargs)
            if check:
                if isinstance(check, HttpUnauthorized):
                    session_auth_result = False
                else:
                    request._authentication_backend = session_auth
                    session_auth_result = check
            else:
                request.user = AnonymousUser()
                session_auth_result = True
            request.user.allowed_tokens = tokens
            return session_auth_result
        if auth_info.startswith('Basic'):
            basic_auth = BasicAuthentication()
            check = basic_auth.is_authenticated(request, **kwargs)
            if check:
                if isinstance(check, HttpUnauthorized):
                    return False
                request._authentication_backend = basic_auth
                return check
        if auth_info.startswith('ApiKey'):
            apikey_auth = ApiKeyAuthentication()
            check = apikey_auth.is_authenticated(request, **kwargs)
            if check:
                if isinstance(check, HttpUnauthorized):
                    return False
                request._authentication_backend = apikey_auth
                return check
        return False

    def get_identifier(self, request):
        try:
            return request._authentication_backend.get_identifier(request)
        except AttributeError:
            return 'nouser'


default_authentication = MyTardisAuthentication()


class ACLAuthorization(Authorization):
    '''Authorisation class for Tastypie.
    '''

    def read_list(self, object_list, bundle):  # noqa # too complex
        obj_ids = [obj.id for obj in object_list]
        if bundle.request.user.is_authenticated and \
           bundle.request.user.is_superuser:
            return object_list
        # Experiments - this should be refactored but not sure how at the mo
        # perhaps with a class->dict key->decorator function
        #
        # CHRIS - added for Project and refactored Dataset to account for new ACLs
        if isinstance(bundle.obj, Experiment):
            experiments = Experiment.safe.all(bundle.request.user)
            return experiments.filter(id__in=obj_ids)
        if isinstance(bundle.obj, ExperimentAuthor):
            experiments = Experiment.safe.all(bundle.request.user)
            return ExperimentAuthor.objects.filter(
                experiment__in=experiments, id__in=obj_ids)
        if isinstance(bundle.obj, ExperimentParameterSet):
            experiments = Experiment.safe.all(bundle.request.user)
            return ExperimentParameterSet.objects.filter(
                experiment__in=experiments, id__in=obj_ids)
        if isinstance(bundle.obj, ExperimentParameter):
            experiments = Experiment.safe.all(bundle.request.user)
            return ExperimentParameter.objects.filter(
                parameterset__experiment__in=experiments,
                id__in=obj_ids
            )
        if isinstance(bundle.obj, Project):
            projects = Project.safe.all(bundle.request.user)
            return projects.filter(id__in=obj_ids)
        if isinstance(bundle.obj, ProjectParameterSet):
            projects = Project.safe.all(bundle.request.user)
            return ProjectParameterSet.objects.filter(
                project__in=projects, id__in=obj_ids)
        if isinstance(bundle.obj, ProjectParameter):
            projects = Project.safe.all(bundle.request.user)
            return ProjectParameter.objects.filter(
                parameterset__project__in=projects,
                id__in=obj_ids
            )
        if isinstance(bundle.obj, Dataset):
            datasets = Dataset.safe.all(bundle.request.user)
            return datasets.filter(id__in=obj_ids)
        if isinstance(bundle.obj, DatasetParameterSet):
            datasets = Dataset.safe.all(bundle.request.user)
            return DatasetParameterSet.objects.filter(
                dataset__in=datasets, id__in=obj_ids)
        if isinstance(bundle.obj, DatasetParameter):
            projects = Dataset.safe.all(bundle.request.user)
            return DatasetParameter.objects.filter(
                parameterset__dataset__in=datasets,
                id__in=obj_ids
            )
        #########################################
        if isinstance(bundle.obj, DataFile):
            all_files = get_accessible_datafiles_for_user(bundle.request)
            return all_files.filter(id__in=obj_ids)
        if isinstance(bundle.obj, DatafileParameterSet):
            datafiles = get_accessible_datafiles_for_user(bundle.request)
            return DatafileParameterSet.objects.filter(
                datafile__in=datafiles, id__in=obj_ids
            )
        if isinstance(bundle.obj, DatafileParameter):
            datafiles = get_accessible_datafiles_for_user(bundle.request)
            return DatafileParameter.objects.filter(
                parameterset__datafile__in=datafiles, id__in=obj_ids)
        if isinstance(bundle.obj, Schema):
            return object_list
        if isinstance(bundle.obj, ParameterName):
            return object_list
        if isinstance(bundle.obj, ObjectACL):
            experiment_ids = Experiment.safe.all(
                bundle.request.user).values_list('id', flat=True)
            return ObjectACL.objects.filter(
                content_type__model='experiment',
                object_id__in=experiment_ids,
                id__in=obj_ids
            )
        if bundle.request.user.is_authenticated and \
                isinstance(bundle.obj, User):
            if facilities_managed_by(bundle.request.user):
                return object_list
            return [user for user in object_list if
                    (user == bundle.request.user or
                     user.experiment_set.filter(public_access__gt=1)
                     .count() > 0)]
        # CHRIS - added for UserProfile and UserAuthentication
        if bundle.request.user.is_authenticated and \
                isinstance(bundle.obj, UserProfile):
            if facilities_managed_by(bundle.request.user):
                return object_list
            return [user for user in object_list if
                    (user == bundle.request.user or
                     user.experiment_set.filter(public_access__gt=1)
                     .count() > 0)]
        if bundle.request.user.is_authenticated and \
                isinstance(bundle.obj, UserAuthentication):
            if facilities_managed_by(bundle.request.user):
                return object_list
            return [user for user in object_list if
                    (user == bundle.request.user or
                     user.experiment_set.filter(public_access__gt=1)
                     .count() > 0)]
        ################################
        if isinstance(bundle.obj, Group):
            if facilities_managed_by(bundle.request.user).count() > 0:
                return object_list
            return bundle.request.user.groups.filter(id__in=obj_ids)
        # CHRIS - added for Institution model
        # All shoould be public for authenticated users
        if isinstance(bundle.obj, Institution):
            if bundle.request.user.is_authenticated:
                return object_list
        ##############################
        if isinstance(bundle.obj, Facility):
            facilities = facilities_managed_by(bundle.request.user)
            return [facility for facility in object_list
                    if facility in facilities]
        if isinstance(bundle.obj, Instrument):
            if bundle.request.user.is_authenticated:
                return object_list
        if isinstance(bundle.obj, StorageBox):
            if bundle.request.user.is_authenticated:
                return object_list
        if isinstance(bundle.obj, StorageBoxOption):
            if bundle.request.user.is_authenticated:
                return [
                    option for option in object_list
                    if option.key in StorageBoxOptionResource.accessible_keys
                ]
        if isinstance(bundle.obj, StorageBoxAttribute):
            if bundle.request.user.is_authenticated:
                return object_list
        return []

    def read_detail(self, object_list, bundle):  # noqa # too complex
        if bundle.request.user.is_authenticated and \
           bundle.request.user.is_superuser:
            return True
        if re.match("^/api/v1/[a-z_]+/schema/$", bundle.request.path):
            return True
        if isinstance(bundle.obj, Experiment):
            return has_access(bundle.request, bundle.obj.id, "experiment")
        if isinstance(bundle.obj, ExperimentAuthor):
            return has_access(
                bundle.request, bundle.obj.experiment.id, "experiment")
        if isinstance(bundle.obj, ExperimentParameterSet):
            return has_access(
                bundle.request, bundle.obj.experiment.id, "experiment")
        if isinstance(bundle.obj, ExperimentParameter):
            return has_access(
                bundle.request, bundle.obj.parameterset.experiment.id, "experiment")
        # CHRIS - Added for Project
        if isinstance(bundle.obj, Project):
            return has_access(bundle.request, bundle.obj.id, "project")
        if isinstance(bundle.obj, ProjectParameterSet):
            return has_access(
                bundle.request, bundle.obj.project.id, "project")
        if isinstance(bundle.obj, ProjectParameter):
            return has_access(
                bundle.request, bundle.obj.parameterset.project.id, "project")
        ###############################
        if isinstance(bundle.obj, Dataset):
            return has_access(bundle.request, bundle.obj.id, "dataset")
        if isinstance(bundle.obj, DatasetParameterSet):
            return has_access(bundle.request, bundle.obj.dataset.id, "dataset")
        if isinstance(bundle.obj, DatasetParameter):
            return has_access(
                bundle.request, bundle.obj.parameterset.dataset.id, "dataset")
        if isinstance(bundle.obj, DataFile):
            return has_access(bundle.request, bundle.obj.id, "datafile")
        if isinstance(bundle.obj, DatafileParameterSet):
            return has_access(
                bundle.request, bundle.obj.datafile.id, "datafile")
        if isinstance(bundle.obj, DatafileParameter):
            return has_access(
                bundle.request, bundle.obj.parameterset.datafile.id, "datafile")
        if isinstance(bundle.obj, User):
            # allow all authenticated users to read public user info
            # the dehydrate function also adds/removes some information
            authenticated = bundle.request.user.is_authenticated
            public_user = bundle.obj.experiment_set.filter(
                public_access__gt=1).count() > 0
            return public_user or authenticated
        # CHRIS - Reproduced User for UserProfile and UserAuthentication
        if isinstance(bundle.obj, UserProfile):
            # allow all authenticated users to read public user info
            # the dehydrate function also adds/removes some information
            authenticated = bundle.request.user.is_authenticated
            public_user = bundle.obj.experiment_set.filter(
                public_access__gt=1).count() > 0
            return public_user or authenticated
        if isinstance(bundle.obj, UserAuthentication):
            # allow all authenticated users to read public user info
            # the dehydrate function also adds/removes some information
            authenticated = bundle.request.user.is_authenticated
            public_user = bundle.obj.experiment_set.filter(
                public_access__gt=1).count() > 0
            return public_user or authenticated
        ##################################
        if isinstance(bundle.obj, Schema):
            return True
        if isinstance(bundle.obj, ParameterName):
            return True
        if isinstance(bundle.obj, StorageBox):
            return bundle.request.user.is_authenticated
        if isinstance(bundle.obj, StorageBoxOption):
            return bundle.request.user.is_authenticated and \
                bundle.obj.key in StorageBoxOptionResource.accessible_keys
        if isinstance(bundle.obj, StorageBoxAttribute):
            return bundle.request.user.is_authenticated
        if isinstance(bundle.obj, Group):
            return bundle.obj in bundle.request.user.groups.all()
        # CHRIS - Added for institutions
        if isinstance(bundle.obj, Institution):
            return bundle.request.user.is_authenticated
        ##########################
        if isinstance(bundle.obj, Facility):
            return bundle.obj in facilities_managed_by(bundle.request.user)
        if isinstance(bundle.obj, Instrument):
            facilities = facilities_managed_by(bundle.request.user)
            return bundle.obj.facility in facilities
        raise NotImplementedError(type(bundle.obj))

    def create_list(self, object_list, bundle):
        raise NotImplementedError(type(bundle.obj))

    def create_detail(self, object_list, bundle):  # noqa # too complex
        if not bundle.request.user.is_authenticated:
            return False
        if bundle.request.user.is_authenticated and \
           bundle.request.user.is_superuser:
            return True
        if isinstance(bundle.obj, Experiment):
            return bundle.request.user.has_perm('tardis_portal.add_experiment')
        if isinstance(bundle.obj, ExperimentAuthor):
            return bundle.request.user.has_perm('tardis_portal.add_experiment')
        if isinstance(bundle.obj, ExperimentParameterSet):
            if not bundle.request.user.has_perm(
                    'tardis_portal.change_experiment'):
                return False
            experiment_uri = bundle.data.get('experiment', None)
            if experiment_uri is not None:
                experiment = ExperimentResource.get_via_uri(
                    ExperimentResource(), experiment_uri, bundle.request)
                return has_write(bundle.request, experiment.id, "experiment")
            if getattr(bundle.obj.experiment, 'id', False):
                return has_write(bundle.request,
                                 bundle.obj.experiment.id, "experiment")
            return False
        if isinstance(bundle.obj, ExperimentParameter):
            return bundle.request.user.has_perm(
                'tardis_portal.change_experiment') and \
                has_write(bundle.request,
                          bundle.obj.parameterset.experiment.id, "experiment")
        #######################################################
        # CHRIS - add stuff for Project Model
        if isinstance(bundle.obj, Project):
            return bundle.request.user.has_perm('tardis_portal.add_project')
        if isinstance(bundle.obj, ProjectParameterSet):
            if not bundle.request.user.has_perm(
                    'tardis_portal.change_project'):
                return False
            project_uri = bundle.data.get('project', None)
            if project_uri is not None:
                project = ProjectResource.get_via_uri(
                    ProjectResource(), project_uri, bundle.request)
                return has_write(bundle.request, project.id, "project")
            if getattr(bundle.obj.project, 'id', False):
                return has_write(bundle.request,
                                 bundle.obj.project.id, "project")
            return False
        if isinstance(bundle.obj, ProjectParameter):
            return bundle.request.user.has_perm(
                'tardis_portal.change_project') and \
                has_write(bundle.request,
                          bundle.obj.parameterset.project.id, "project")
        ####################################
        if isinstance(bundle.obj, Dataset):
            if not bundle.request.user.has_perm(
                    'tardis_portal.change_dataset'):
                return False
            perm = False
            for exp_uri in bundle.data.get('experiments', []):
                try:
                    this_exp = ExperimentResource.get_via_uri(
                        ExperimentResource(), exp_uri, bundle.request)
                except:
                    return False
                if has_write(bundle.request, this_exp.id, "experiment"):
                    perm = True
                else:
                    return False
            return perm
        if isinstance(bundle.obj, DatasetParameterSet):
            if not bundle.request.user.has_perm(
                    'tardis_portal.change_dataset'):
                return False
            dataset_uri = bundle.data.get('dataset', None)
            if dataset_uri is not None:
                dataset = DatasetResource.get_via_uri(
                    DatasetResource(), dataset_uri, bundle.request)
                return has_write(bundle.request, dataset.id, "dataset")
            if getattr(bundle.obj.dataset, 'id', False):
                return has_write(bundle.request,
                                 bundle.obj.dataset.id, "dataset")
            return False
        if isinstance(bundle.obj, DatasetParameter):
            return bundle.request.user.has_perm(
                'tardis_portal.change_dataset') and \
                has_write(bundle.request,
                          bundle.obj.parameterset.dataset.id, "dataset")

        if isinstance(bundle.obj, DataFile):
            dataset = DatasetResource.get_via_uri(DatasetResource(),
                                                  bundle.data['dataset'],
                                                  bundle.request)
            return all([
                bundle.request.user.has_perm('tardis_portal.change_dataset'),
                bundle.request.user.has_perm('tardis_portal.add_datafile'),
                has_write(bundle.request, dataset.id, "dataset"),
            ])
        if isinstance(bundle.obj, DatafileParameterSet):
            datafile = DataFile.objects.get(
                pk=bundle.obj.datafile.id)
            return all([
                bundle.request.user.has_perm('tardis_portal.change_datafile'),
                bundle.request.user.has_perm('tardis_portal.add_datafile'),
                has_write(bundle.request, datafile.id, "datafile"),
            ])
        if isinstance(bundle.obj, DatafileParameter):
            datafile = DataFile.objects.get(
                pk=bundle.obj.parameterset.datafile.id)
            return all([
                bundle.request.user.has_perm('tardis_portal.change_datafile'),
                bundle.request.user.has_perm('tardis_portal.add_datafile'),
                has_write(bundle.request, datafile.id, "datafile"),
            ])
        if isinstance(bundle.obj, DataFileObject):
            return all([
                bundle.request.user.has_perm('tardis_portal.change_datafile'),
                bundle.request.user.has_perm('tardis_portal.add_datafile'),
                has_write(bundle.request,
                          bundle.obj.datafile.id, "datafile"),
            ])

        if isinstance(bundle.obj, ObjectACL):
            return bundle.request.user.has_perm('tardis_portal.add_objectacl')
        if isinstance(bundle.obj, Group):
            return bundle.request.user.has_perm('tardis_portal.add_group')
        if isinstance(bundle.obj, Facility):
            return bundle.request.user.has_perm('tardis_portal.add_facility')
        # CHRIS - Add check for institutions
        if isinstance(bundle.obj, Institution):
            return bundle.request.user.has_perm('tardis_portal.add_insitution')
        #############
        if isinstance(bundle.obj, Instrument):
            facilities = facilities_managed_by(bundle.request.user)
            return all([
                bundle.request.user.has_perm('tardis_portal.add_instrument'),
                bundle.obj.facility in facilities
            ])
        # CHRIS - Add for User
        if isinstance(bundle.obj, User):
            return all([
                bundle.request.user.has_perm('tardis_portal.add_userprofile'),
                bundle.request.user.has_perm(
                    'tardis_portal.add_userauthentication')
            ])
        # if isinstance(bundle.obj, UserProfile):
        #    return all([
        #        bundle.request.user.has_perm('tardis_portal.add_userprofile'),
        #        bundle.request.user.has_perm('tardis_portal.add_userauthentication')
        #        ])
        # if isinstance(bundle.obj, UserAuthentication):
        #    return all([
        #        bundle.request.user.has_perm('tardis_portal.add_userprofile'),
        #        bundle.request.user.has_perm('tardis_portal.add_userauthentication')
        #        ])
        ################################
        raise NotImplementedError(type(bundle.obj))

    def update_list(self, object_list, bundle):
        raise NotImplementedError(type(bundle.obj))
        # allowed = []

        # # Since they may not all be saved, iterate over them.
        # for obj in object_list:
        #     if obj.user == bundle.request.user:
        #         allowed.append(obj)

        # return allowed

    def update_detail(self, object_list, bundle):  # noqa # too complex
        '''
        Latest TastyPie requires update_detail permissions to be able to create
        objects.  Rather than duplicating code here, we'll just use the same
        authorization rules we use for create_detail.
        '''
        return self.create_detail(object_list, bundle)

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")

    # CHRIS - This should probably be refactored for more fine-grained control
    # or to push up to Project
    def delete_detail(self, object_list, bundle):
        if isinstance(bundle.obj, Experiment):
            return bundle.request.user.has_perm(
                'tardis_portal.change_experiment') and \
                has_delete_permissions(bundle.request, bundle.obj.id)
        raise Unauthorized("Sorry, no deletes.")


class GroupResource(ModelResource):
    class Meta:
        object_class = Group
        queryset = Group.objects.all()
        authentication = default_authentication
        authorization = ACLAuthorization()
        filtering = {
            'id': ('exact',),
            'name': ('exact',),
        }


class UserResource(ModelResource):
    groups = fields.ManyToManyField(GroupResource, 'groups',
                                    null=True, full=True)

    class Meta:
        object_class = User
        authentication = default_authentication
        authorization = ACLAuthorization()
        queryset = User.objects.all()
        allowed_methods = ['get',
                           'post',
                           'put']
        fields = ['id',
                  'username',
                  'first_name',
                  'last_name',
                  'email']
        serializer = default_serializer
        filtering = {
            'id': ('exact', ),
            'username': ('exact', ),
            'email': ('iexact', ),
        }

    def dehydrate(self, bundle):
        '''
        use cases::
          public user:
            anonymous:
              name, uri, email, id
            authenticated:
              other user:
                name, uri, email, id [, username if facility manager]
              same user:
                name, uri, email, id, username
          private user:
            anonymous:
              none
            authenticated:
              other user:
                name, uri, id [, username, email if facility manager]
              same user:
                name, uri, email, id, username
        '''
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated
        queried_user = bundle.obj
        public_user = queried_user.experiment_set.filter(
            public_access__gt=1).count() > 0
        same_user = authuser == queried_user

        # add the database id for convenience
        bundle.data['id'] = queried_user.id

        # allow the user to find out their username and email
        # allow facility managers to query other users' username and email
        if authenticated and \
                (same_user or facilities_managed_by(authuser).count() > 0):
            bundle.data['username'] = queried_user.username
            bundle.data['email'] = queried_user.email
        else:
            del(bundle.data['username'])
            del(bundle.data['email'])

        # add public information
        if public_user:
            bundle.data['email'] = queried_user.email

        return bundle

    # CHRIS - open user to API - generate random password which no one knows
    # since all authentication will be handled through LDAP
    def hydrate(self, bundle):
        required_fields = ['username',
                           'first_name',
                           'email',
                           'permissions',
                           'auth_method']
        for field in required_fields:
            if field not in bundle.data:
                raise KeyError
        bundle.data["password"] = make_password(self.gen_random_password())
        return bundle

    def gen_random_password(self):
        import random
        random.seed()
        characters = 'abcdefghijklmnopqrstuvwxyzABCDFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?'
        passlen = 16
        password = "".join(random.sample(characters, passlen))
        return password

    def obj_create(self,
                   bundle,
                   **kwargs):
        try:
            email = bundle.data["email"]
            username = bundle.data["username"]
            if User.objects.filter(email=email):
                raise Exception(
                    message="User cannot be created as the supplied email is already used.")
            if User.objects.filter(username=username):
                raise Exception(
                    message="User cannot be created as the supplied username is already used.")
        except KeyError as missing_key:
            raise Exception(
                message="Must provide {missing_key} when creating a user."
                        .format(missing_key=missing_key))
        except User.DoesNotExist:
            pass
        permissions = bundle.data['permissions']
        auth_method = bundle.data['auth_method']
        bundle.obj = User.objects.create_user(
            username, email, bundle.data['password'])
        bundle.obj.first_name = bundle.data['first_name']
        if 'last_name' in bundle.data.keys():
            bundle.obj.last_name = bundle.data['last_name']
        for permission in permissions:
            bundle.obj.user_permissions.add(
                Permission.objects.get(codename=permission))
        bundle.obj.save()  # create the user - this should also trigger the UserProfile
        userprofile = bundle.obj.userprofile
        if 'orcid' in bundle.data.keys():
            userprofile.orcid = bundle.data['orcid']
            userprofile.save()
        user_auth = UserAuthentication(userProfile=userprofile,
                                       username=username,
                                       authenticationMethod=auth_method)
        user_auth.save()
        return bundle
    ############################################################


class MyTardisModelResource(ModelResource):

    class Meta:
        authentication = default_authentication
        authorization = ACLAuthorization()
        serializer = default_serializer
        object_class = None

# CHRIS - refactored to account for the new model


class InstitutionResource(MyTardisModelResource):
    manager_group = fields.ForeignKey(GroupResource, 'manager_group',
                                      null=True, full=True)

    class Meta(MyTardisModelResource.Meta):
        object_class = Institution
        queryset = Institution.objects.all()
        filtering = {
            'id': ('exact', ),
            'manager_group': ALL_WITH_RELATIONS,
            'name': ('exact', ),
            'url': ('exact', ),
            'ror': ('exact', ),
        }
        ordering = [
            'id',
            'name'
        ]
        always_return_data = True


class FacilityResource(MyTardisModelResource):
    manager_group = fields.ForeignKey(GroupResource, 'manager_group',
                                      null=True, full=True)
    institution = fields.ForeignKey(InstitutionResource, 'institution',
                                    null=True, full=True)

    class Meta(MyTardisModelResource.Meta):
        object_class = Facility
        queryset = Facility.objects.all()
        filtering = {
            'id': ('exact', ),
            'manager_group': ALL_WITH_RELATIONS,
            'name': ('exact', ),
            'url': ('exact', ),
            'institution': ALL_WITH_RELATIONS,
        }
        ordering = [
            'id',
            'name'
        ]
        always_return_data = True
###########################################

# CHRIS - ProjectResource


class ProjectResource(MyTardisModelResource):
    '''API for Projects
    also creates a default ACL and allows ProjectParameterSets to be read
    and written.

    TODO: catch duplicate schema submissions for parameter sets
    '''
    created_by = fields.ForeignKey(UserResource, 'created_by')
    parameter_sets = fields.ToManyField(
        'tardis.tardis_portal.api.ProjectParameterSetResource',
        'projectparameterset_set',
        related_name='project',
        full=True, null=True)
    institution = fields.ToManyField(InstitutionResource, 'institution',
                                     null=True, full=True)
    lead_researcher = fields.ForeignKey(UserResource, 'lead_researcher')

    class Meta(MyTardisModelResource.Meta):
        object_class = Project
        queryset = Project.objects.all()
        filtering = {
            'id': ('exact', ),
            'name': ('exact',),
            'raid': ('exact',),
            'url': ('exact',),
            'institution': ALL_WITH_RELATIONS,
        }
        ordering = [
            'id',
            'name',
            'url',
            'start_date',
            'end_date'
        ]
        always_return_data = True

    def dehydrate(self, bundle):
        project = bundle.obj
        admins = project.get_admins()
        bundle.data['admin_groups'] = [acl.id for acl in admins]
        members = project.get_groups()
        bundle.data['member_groups'] = [acl.id for acl in members]
        return bundle

    def hydrate_m2m(self, bundle):
        '''
        create ACL before any related objects are created in order to use
        ACL permissions for those objects.
        '''
        project_groups = []
        project_admin_groups = []
        project_admin_users = []
        if getattr(bundle.obj, 'id', False):
            project = bundle.obj
            project_lead = project.lead_researcher
            # TODO: unify this with the view function's ACL creation,
            # maybe through an ACL toolbox.
            create_acl(project.get_ct(),
                       project.id,
                       django_user,
                       str(bundle.request.user.id),
                       admin=True)
            create_acl(project.get_ct(),
                       project.id,
                       django_user,
                       str(project_lead.id),
                       admin=True)
            if 'admin_groups' in bundle.data.keys():
                for grp in bundle.data['admin_groups']:
                    group, created = Group.objects.get_or_create(name=grp)
                    project_admin_groups.append(group)
                    project_groups.append(group)
                    if created:
                        group.permissions.set(admin_perms)
                    create_acl(project.get_ct(),
                               project.id,
                               django_group,
                               group.id,
                               admin=True)
                bundle.data.pop('admin_groups')
            if 'member_groups' in bundle.data.keys():
                # Each member group is defined by a tuple
                # (group_name, sensitive[T/F], download[T/F])
                # unpack for ACLs
                for grp in bundle.data['member_groups']:
                    grp_name = grp[0]
                    sensitive_flg = grp[1]
                    download_flg = grp[2]
                    group, created = Group.objects.get_or_create(name=grp_name)
                    project_groups.append(group)
                    if created:
                        group.permissions.set(member_perms)
                    create_acl(project.get_ct(),
                               project.id,
                               django_group,
                               group.id,
                               write=True,
                               download=download_flg,
                               sensitive=sensitive_flg,
                               admin=False)
                bundle.data.pop('member_groups')
            if 'admins' in bundle.data.keys():
                for admin in bundle.data['admins']:
                    if not User.objects.filter(username=admin).exists():
                        new_user = get_user_from_upi(admin)
                        user = User.objects.create(username=new_user['username'],
                                                   first_name=new_user['first_name'],
                                                   last_name=new_user['last_name'],
                                                   email=new_user['email'])
                        user.set_password(gen_random_password())
                        for permission in admin_perms:
                            user.user_permissions.add(permission)
                        user.save()
                        authentication = UserAuthentication(userProfile=user.userprofile,
                                                            username=new_user['username'],
                                                            authenticationMethod=settings.LDAP_METHOD)
                        authentication.save()
                    user = User.objects.get(username=admin)
                    project_admin_users.append(user)
                    create_acl(project.get_ct(),
                               project.id,
                               django_user,
                               user.id,
                               admin=True)
                bundle.data.pop('admins')
            if 'members' in bundle.data.keys():
                for member in bundle.data['members']:
                    member_name = member[0]
                    sensitive_flg = member[1]
                    download_flg = member[2]
                    if not User.objects.filter(username=member_name).exists():
                        new_user = get_user_from_upi(member_name)
                        if not new_user:
                            logger.error('No one found for upi: {member}')
                        user = User.objects.create(username=new_user['username'],
                                                   first_name=new_user['first_name'],
                                                   last_name=new_user['last_name'],
                                                   email=new_user['email'])
                        user.set_password(gen_random_password())
                        for permission in member_perms:
                            user.user_permissions.add(permission)
                        user.save()
                        authentication = UserAuthentication(userProfile=user.userprofile,
                                                            username=new_user['username'],
                                                            authenticationMethod=settings.LDAP_METHOD)
                        authentication.save()
                    user = User.objects.get(username=member_name)
                    create_acl(project.get_ct(),
                               project.id,
                               django_user,
                               user.id,
                               write=True,
                               download=download_flg,
                               sensitive=sensitive_flg,
                               admin=False)
                bundle.data.pop('members')
            for group in project_groups:
                group_admin, _ = GroupAdmin.objects.get_or_create(user=bundle.request.user,
                                                                  group=group)
                for admin in project_admin_groups:
                    group_admin.admin_groups.add(admin.id)
                for admin in project_admin_users:
                    group_admin.admin_users.add(admin.id)
        return super().hydrate_m2m(bundle)

    def obj_create(self, bundle, **kwargs):
        '''Currently not tested for failed db transactions as sqlite does not
        enforce limits.
        '''
        user = bundle.request.user
        bundle.data['created_by'] = user
        logger.error('Pre processed bundle')
        logger.error(bundle.data)
        project_lead = User.objects.get(
            username=bundle.data['lead_researcher'])
        bundle.data['lead_researcher'] = project_lead
        bundle = super().obj_create(bundle, **kwargs)
        return bundle
################################################


class InstrumentResource(MyTardisModelResource):
    facility = fields.ForeignKey(FacilityResource, 'facility',
                                 null=True, full=True)

    class Meta(MyTardisModelResource.Meta):
        object_class = Instrument
        queryset = Instrument.objects.all()
        filtering = {
            'id': ('exact', ),
            'facility': ALL_WITH_RELATIONS,
            'name': ('exact', ),
            'instrument_id': ('exact', ),
        }
        ordering = [
            'id',
            'name',
            'instrument_id',
        ]
        always_return_data = True


class ExperimentResource(MyTardisModelResource):
    '''API for Experiments
    also creates a default ACL and allows ExperimentParameterSets to be read
    and written.

    TODO: catch duplicate schema submissions for parameter sets
    '''
    created_by = fields.ForeignKey(UserResource, 'created_by')
    parameter_sets = fields.ToManyField(
        'tardis.tardis_portal.api.ExperimentParameterSetResource',
        'experimentparameterset_set',
        related_name='experiment',
        full=True, null=True)
    project = fields.ForeignKey(ProjectResource,
                                'project',
                                full=True,
                                null=True)

    class Meta(MyTardisModelResource.Meta):
        object_class = Experiment
        queryset = Experiment.objects.all()
        filtering = {
            'id': ('exact', ),
            'title': ('exact',),
            'raid': ('exact',),
            'project': ALL_WITH_RELATIONS,
        }
        ordering = [
            'id',
            'title',
            'id',
            'project',
            'created_time',
            'update_time'
        ]
        always_return_data = True

    def dehydrate(self, bundle):
        exp = bundle.obj
        authors = [{'name': a.author, 'url': a.url}
                   for a in exp.experimentauthor_set.all()]
        bundle.data['authors'] = authors
        lic = exp.license
        if lic is not None:
            bundle.data['license'] = {
                'name': lic.name,
                'url': lic.url,
                'description': lic.internal_description,
                'image_url': lic.image_url,
                'allows_distribution': lic.allows_distribution,
            }
        owners = exp.get_owners()
        bundle.data['owner_ids'] = [o.id for o in owners]
        admins = exp.get_admins()
        bundle.data['admin_groups'] = [grp.id for grp in admins]
        members = exp.get_groups()
        bundle.data['member_groups'] = [grp.id for grp in members]
        return bundle

    def hydrate_m2m(self, bundle):
        '''
        create ACL before any related objects are created in order to use
        ACL permissions for those objects.
        '''
        if getattr(bundle.obj, 'id', False):
            try:
                project = ProjectResource.get_via_uri(
                    ProjectResource(), bundle.data['project'], bundle.request)
            except NotFound:
                raise  # This probably should raise an error
        experiment_groups = []
        experiment_admin_groups = []
        experiment_admin_users = []
        if getattr(bundle.obj, 'id', False):
            experiment = bundle.obj
            project_lead = project.lead_researcher
            # TODO: unify this with the view function's ACL creation,
            # maybe through an ACL toolbox.
            acl = ObjectACL(content_type=experiment.get_ct(),
                            object_id=experiment.id,
                            pluginId=django_user,
                            entityId=str(project_lead.id),
                            canRead=True,
                            canDownload=True,
                            canWrite=True,
                            canDelete=True,
                            canSensitive=True,
                            isOwner=True,
                            aclOwnershipType=ObjectACL.OWNER_OWNED)
            acl.save()
            if 'admin_groups' in bundle.data.keys():
                admin_groups = bundle.data.pop('admin_groups')
            else:
                admin_groups = project.get_admins()
            if admin_groups != []:
                for grp in admin_groups:
                    group, created = Group.objects.get_or_create(name=grp)
                    experiment_admin_groups.append(group)
                    experiment_groups.append(group)
                    if created:
                        group.permissions.set(admin_perms)
                        create_acl(experiment.get_ct(),
                                   experiment.id,
                                   django_group,
                                   group.id,
                                   admin=True)
                    if group not in Project.safe.groups(project.id):
                        create_acl(project.get_ct(),
                                   project.id,
                                   django_group,
                                   group.id)
            if 'member_groups' in bundle.data.keys():
                member_groups = bundle.data.pop('member_groups')
            else:
                member_groups = project.get_groups_and_perms()
                # Each member group is defined by a tuple
                # (group_name, sensitive[T/F], download[T/F])
                # unpack for ACLs
                logger.error("Groups to append: {}".format(member_groups))
            if member_groups != []:
                for grp in member_groups:
                    grp_name = grp[0]
                    sensitive_flg = grp[1]
                    download_flg = grp[2]
                    group, created = Group.objects.get_or_create(name=grp_name)
                    experiment_groups.append(group)
                    if created:
                        group.permissions.set(member_perms)
                    create_acl(experiment.get_ct(),
                               experiment.id,
                               django_group,
                               group.id,
                               write=True,
                               download=download_flg,
                               sensitive=sensitive_flg,
                               admin=False)
                    if group not in Project.safe.groups(project.id):
                        create_acl(project.get_ct(),
                                   project.id,
                                   django_group,
                                   group.id)
            if 'admins' in bundle.data.keys():
                if bundle.data['admins'] != []:
                    for admin in bundle.data['admins']:
                        logger.error(admin)
                        if not User.objects.filter(username=admin).exists():
                            new_user = get_user_from_upi(admin)
                            user = User.objects.create(username=new_user['username'],
                                                       first_name=new_user['first_name'],
                                                       last_name=new_user['last_name'],
                                                       email=new_user['email'])
                            user.set_password(gen_random_password())
                            for permission in admin_perms:
                                user.user_permissions.add(permission)
                            user.save()
                            authentication = UserAuthentication(userProfile=user.userprofile,
                                                                username=new_user['username'],
                                                                authenticationMethod=settings.LDAP_METHOD)
                            authentication.save()
                        user = User.objects.get(username=admin)
                        experiment_admin_users.append(user)
                        create_acl(experiment.get_ct(),
                                   experiment.id,
                                   django_user,
                                   user.id,
                                   admin=True)
                        if user not in Project.safe.users(project.id):
                            create_acl(project.get_ct(),
                                       project.id,
                                       django_user,
                                       user.id)
                bundle.data.pop('admins')
            else:
                # Cascade the admin from the project level
                project_admins = project.get_owners()
                for user in project_admins:
                    if user.username == project.lead_researcher:
                        # Lead researchers get all perms
                        continue
                    add_flg = True
                    if 'members' in bundle.data.keys():
                        for member in bundle.data['members']:
                            if user.username == member[0]:
                                # Don't add this user to the admin group since they have implicitly
                                # been downgraded
                                add_flg = False
                    if add_flg:
                        create_acl(experiment.get_ct(),
                                   experiment.id,
                                   django_user,
                                   user.id,
                                   admin=True)
                        # No need to check traverse since they have admin rights in parent
            if 'members' in bundle.data.keys():
                # error checking needs to be done externally for this to
                # function as desired.
                if bundle.data['members'] != []:
                    members = bundle.data['members']
                    for member in members:
                        logger.error(member)
                        member_name = member[0]
                        sensitive_flg = member[1]
                        download_flg = member[2]
                        if not User.objects.filter(username=member_name).exists():
                            new_user = get_user_from_upi(member_name)
                            if not new_user:
                                logger.error(
                                    "No one found for upi: {}".format(member_name))
                            user = User.objects.create(username=new_user['username'],
                                                       first_name=new_user['first_name'],
                                                       last_name=new_user['last_name'],
                                                       email=new_user['email'])
                            user.set_password(gen_random_password())
                            for permission in member_perms:
                                user.user_permissions.add(permission)
                            user.save()
                            authentication = UserAuthentication(userProfile=user.userprofile,
                                                                username=new_user['username'],
                                                                authenticationMethod=settings.LDAP_METHOD)
                            authentication.save()
                        user = User.objects.get(username=member_name)
                        create_acl(experiment.get_ct(),
                                   experiment.id,
                                   django_user,
                                   user.id,
                                   write=True,
                                   download=download_flg,
                                   sensitive=sensitive_flg,
                                   admin=False)
                        if user not in Project.safe.users(project.id):
                            create_acl(project.get_ct(),
                                       project.id,
                                       django_user,
                                       user.id)
                bundle.data.pop('members')
            else:
                project_members = project.get_users_and_perms()
                for user_tuple in project_members:
                    user, sensitive, download = user_tuple
                    if user.username == project.lead_researcher:
                        # Lead researchers get all perms
                        continue
                    create_acl(experiment.get_ct(),
                               experiment.id,
                               django_user,
                               user.id,
                               write=True,
                               download=download,
                               sensitive=sensitive,
                               admin=False)
        for group in experiment_groups:
            logger.error("Creating group admin for {}".format(group))
            group_admin, _ = GroupAdmin.objects.get_or_create(user=bundle.request.user,
                                                              group=group)
            for admin in experiment_admin_groups:
                group_admin.admin_groups.add(admin.id)
            for admin in experiment_admin_users:
                group_admin.admin_users.add(admin.id)
            logger.error(group_admin)
        return super().hydrate_m2m(bundle)

    def obj_create(self, bundle, **kwargs):
        '''experiments need at least one ACL to be available through the
        ExperimentManager (Experiment.safe)
        Currently not tested for failed db transactions as sqlite does not
        enforce limits.
        '''
        user = bundle.request.user
        bundle.data['created_by'] = user
        bundle = super().obj_create(bundle, **kwargs)
        return bundle


class ExperimentAuthorResource(MyTardisModelResource):
    '''API for ExperimentAuthors
    '''
    experiment = fields.ForeignKey(
        ExperimentResource, 'experiment', full=True, null=True)

    class Meta(MyTardisModelResource.Meta):
        object_class = ExperimentAuthor
        queryset = ExperimentAuthor.objects.all()
        filtering = {
            'id': ('exact', ),
            'experiment': ALL_WITH_RELATIONS,
            'author': ('exact', 'iexact'),
            'institution': ('exact', 'iexact'),
            'email': ('exact', 'iexact'),
            'order': ('exact',),
            'url': ('exact', 'iexact'),
        }
        ordering = [
            'id',
            'author',
            'email',
            'order'
        ]
        always_return_data = True

# CHRIS - Dataset needs ACLs created


class DatasetResource(MyTardisModelResource):
    experiments = fields.ToManyField(
        ExperimentResource, 'experiments', related_name='datasets')
    parameter_sets = fields.ToManyField(
        'tardis.tardis_portal.api.DatasetParameterSetResource',
        'datasetparameterset_set',
        related_name='dataset',
        full=True, null=True)
    instrument = fields.ForeignKey(
        InstrumentResource,
        'instrument',
        null=True,
        full=True)

    class Meta(MyTardisModelResource.Meta):
        object_class = Dataset
        queryset = Dataset.objects.all()
        filtering = {
            'id': ('exact', ),
            'experiments': ALL_WITH_RELATIONS,
            'description': ('exact', ),
            'directory': ('exact', ),
            'instrument': ALL_WITH_RELATIONS,
            'dataset_id': ('exact', ),
        }
        ordering = [
            'id',
            'description'
        ]
        always_return_data = True

    def dehydrate(self, bundle):
        dataset = bundle.obj
        admins = dataset.get_admins()
        bundle.data['admin_groups'] = [acl.id for acl in admins]
        members = dataset.get_groups()
        bundle.data['member_groups'] = [acl.id for acl in members]
        return bundle

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/files/'
                r'(?:(?P<file_path>.+))?$' % self._meta.resource_name,
                self.wrap_view('get_datafiles'),
                name='api_get_datafiles_for_dataset'),

            url(r'^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/root-dir-nodes%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_root_dir_nodes'),
                name='api_get_root_dir_nodes'),
            url(r'^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/child-dir-nodes%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_child_dir_nodes'),
                name='api_get_child_dir_nodes'),
        ]

    def get_datafiles(self, request, **kwargs):
        file_path = kwargs.get('file_path', None)
        dataset_id = kwargs['pk']

        datafiles = DataFile.objects.filter(dataset__id=dataset_id)
        auth_bundle = self.build_bundle(request=request)
        auth_bundle.obj = DataFile()
        self.authorized_read_list(
            datafiles, auth_bundle
        )
        del kwargs['pk']
        del kwargs['file_path']
        kwargs['dataset__id'] = dataset_id
        if file_path is not None:
            kwargs['directory__startswith'] = file_path
        df_res = DataFileResource()
        return df_res.dispatch('list', request, **kwargs)

    def hydrate_m2m(self, bundle):
        '''
        Create experiment-dataset associations first, because they affect
        authorization for adding other related resources, e.g. metadata
        '''
        if getattr(bundle.obj, 'id', False):
            for exp_uri in bundle.data.get('experiments', []):
                try:
                    exp = ExperimentResource.get_via_uri(
                        ExperimentResource(), exp_uri, bundle.request)
                    bundle.obj.experiments.add(exp)
                except NotFound:
                    pass  # This probably should raise an error
        if getattr(bundle.obj, 'id', False):
            dataset = bundle.obj
            # There should only be one expt
            try:
                experiment_uri = bundle.data['experiments'][0]
                experiment = ExperimentResource.get_via_uri(
                    ExperimentResource(), experiment_uri, bundle.request)
            except NotFound:
                logger.error(
                    "Unable to locate parent experiment for {}".format(bundle.data["description"]))
                raise
            project = experiment.project
            project_lead = project.lead_researcher
            dataset_admin_groups = []
            dataset_groups = []
            dataset_admin_users = []
            # TODO: unify this with the view function's ACL creation,
            # maybe through an ACL toolbox.
            acl = ObjectACL(content_type=dataset.get_ct(),
                            object_id=dataset.id,
                            pluginId=django_user,
                            entityId=str(project_lead.id),
                            canRead=True,
                            canDownload=True,
                            canWrite=True,
                            canDelete=True,
                            canSensitive=True,
                            isOwner=True,
                            aclOwnershipType=ObjectACL.OWNER_OWNED)
            acl.save()
            if 'admin_groups' in bundle.data.keys():
                admin_groups = bundle.data.pop('admin_groups')
            else:
                admin_groups = experiment.get_admins()
            if admin_groups != []:
                for grp in admin_groups:
                    group, created = Group.objects.get_or_create(name=grp)
                    dataset_admin_groups.append(group)
                    dataset_groups.append(group)
                    if created:
                        group.permissions.set(admin_perms)
                        create_acl(dataset.get_ct(),
                                   dataset.id,
                                   django_group,
                                   group.id,
                                   admin=True)
                    if group not in Project.safe.groups(project.id):
                        create_acl(project.get_ct(),
                                   project.id,
                                   django_group,
                                   group.id)
                    if group not in Experiment.safe.groups(experiment.id):
                        create_acl(experiment.get_ct(),
                                   experiment.id,
                                   django_group,
                                   group.id)
            if 'member_groups' in bundle.data.keys():
                member_groups = bundle.data.pop('member_groups')
            else:
                member_groups = experiment.get_groups_and_perms()
                # Each member group is defined by a tuple
                # (group_name, sensitive[T/F], download[T/F])
                # unpack for ACLs
                logger.error("Groups to append: {}".format(member_groups))
            if member_groups != []:
                for grp in member_groups:
                    grp_name = grp[0]
                    sensitive_flg = grp[1]
                    download_flg = grp[2]
                    group, created = Group.objects.get_or_create(name=grp_name)
                    dataset_groups.append(group)
                    if created:
                        group.permissions.set(member_perms)
                    create_acl(dataset.get_ct(),
                               dataset.id,
                               django_group,
                               group.id,
                               write=True,
                               download=download_flg,
                               sensitive=sensitive_flg,
                               admin=False)
                    if group not in Project.safe.groups(project.id):
                        create_acl(project.get_ct(),
                                   project.id,
                                   django_group,
                                   group.id)
                    if group not in Experiment.safe.groups(experiment.id):
                        create_acl(experiment.get_ct(),
                                   experiment.id,
                                   django_group,
                                   group.id)
            if 'admins' in bundle.data.keys():
                if bundle.data['admins'] != []:
                    for admin in bundle.data['admins']:
                        logger.error(admin)
                        if not User.objects.filter(username=admin).exists():
                            new_user = get_user_from_upi(admin)
                            user = User.objects.create(username=new_user['username'],
                                                       first_name=new_user['first_name'],
                                                       last_name=new_user['last_name'],
                                                       email=new_user['email'])
                            user.set_password(gen_random_password())
                            for permission in admin_perms:
                                user.user_permissions.add(permission)
                            user.save()
                            authentication = UserAuthentication(userProfile=user.userprofile,
                                                                username=new_user['username'],
                                                                authenticationMethod=settings.LDAP_METHOD)
                            authentication.save()
                        user = User.objects.get(username=admin)
                        dataset_admin_users.append(user)
                        create_acl(dataset.get_ct(),
                                   dataset.id,
                                   django_user,
                                   user.id,
                                   admin=True)
                        if user not in Project.safe.users(project.id):
                            create_acl(project.get_ct(),
                                       project.id,
                                       django_user,
                                       user.id)
                        if user not in Experiment.safe.users(experiment.id):
                            create_acl(experiment.get_ct(),
                                       experiment.id,
                                       django_user,
                                       user.id)
                bundle.data.pop('admins')
            else:
                # Cascade the admin from the project level
                experiment_admins = experiment.get_owners()
                for user in experiment_admins:
                    if user.username == project.lead_researcher:
                        # Lead researchers get all perms
                        continue
                    add_flg = True
                    if 'members' in bundle.data.keys():
                        for member in bundle.data['members']:
                            if user.username == member[0]:
                                # Don't add this user to the admin group since they have implicitly
                                # been downgraded
                                add_flg = False
                    if add_flg:
                        create_acl(dataset.get_ct(),
                                   dataset.id,
                                   django_user,
                                   user.id,
                                   admin=True)
                        # No need to check traverse since they have admin rights in parent
            if 'members' in bundle.data.keys():
                # error checking needs to be done externally for this to
                # function as desired.
                if bundle.data['members'] != []:
                    members = bundle.data['members']
                    for member in members:
                        logger.error(member)
                        member_name = member[0]
                        sensitive_flg = member[1]
                        download_flg = member[2]
                        if not User.objects.filter(username=member_name).exists():
                            new_user = get_user_from_upi(member_name)
                            if not new_user:
                                logger.error(
                                    "No one found for upi: {}".format(member_name))
                            user = User.objects.create(username=new_user['username'],
                                                       first_name=new_user['first_name'],
                                                       last_name=new_user['last_name'],
                                                       email=new_user['email'])
                            user.set_password(gen_random_password())
                            for permission in member_perms:
                                user.user_permissions.add(permission)
                            user.save()
                            authentication = UserAuthentication(userProfile=user.userprofile,
                                                                username=new_user['username'],
                                                                authenticationMethod=settings.LDAP_METHOD)
                            authentication.save()
                        user = User.objects.get(username=member_name)
                        create_acl(dataset.get_ct(),
                                   dataset.id,
                                   django_user,
                                   user.id,
                                   write=True,
                                   download=download_flg,
                                   sensitive=sensitive_flg,
                                   admin=False)
                        if user not in Project.safe.users(project.id):
                            create_acl(project.get_ct(),
                                       project.id,
                                       django_user,
                                       user.id)
                        if user not in Experiment.safe.users(project.id):
                            create_acl(experiment.get_ct(),
                                       experiment.id,
                                       django_user,
                                       user.id)
                bundle.data.pop('members')
            else:
                experiment_members = experiment.get_users_and_perms()
                for user_tuple in experiment_members:
                    user, sensitive, download = user_tuple
                    if user.username == project.lead_researcher:
                        # Lead researchers get all perms
                        continue
                    create_acl(dataset.get_ct(),
                               dataset.id,
                               django_user,
                               user.id,
                               write=True,
                               download=download,
                               sensitive=sensitive,
                               admin=False)
        for group in dataset_groups:
            logger.error("Creating group admin for {}".format(group))
            group_admin, _ = GroupAdmin.objects.get_or_create(user=bundle.request.user,
                                                              group=group)
            for admin in dataset_admin_groups:
                group_admin.admin_groups.add(admin.id)
            for admin in dataset_admin_users:
                group_admin.admin_users.add(admin.id)
            logger.error(group_admin)
        return super().hydrate_m2m(bundle)

    def get_root_dir_nodes(self, request, **kwargs):
        '''Return JSON-serialized list of filenames/folders in the dataset's root directory
        '''
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)

        dataset_id = kwargs['pk']
        dataset = Dataset.objects.get(id=dataset_id)
        # get dirs at root level
        dir_tuples = dataset.get_dir_tuples(request.user, basedir="")
        # get files at root level
        dfs = (DataFile.safe.all(request.user).filter(dataset=dataset, directory='') |
               DataFile.safe.all(request.user).filter(dataset=dataset, directory__isnull=True)).distinct()
        child_list = []
        # append directories list
        if dir_tuples:
            for dir_tuple in dir_tuples:
                child_dict = {
                    'name': dir_tuple[0],
                    'path': dir_tuple[1],
                    'children': []
                }
                child_list.append(child_dict)
                # append files to list
        if dfs:
            filenames = [df.filename for df in dfs]
            for filename in filenames:
                children = {}
                children['name'] = filename
                child_list.append(children)

        return JsonResponse(child_list, status=200, safe=False)

    def get_child_dir_nodes(self, request, **kwargs):
        '''Return JSON-serialized list of filenames/folders within a child subdirectory
        '''
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)

        dataset_id = kwargs['pk']
        tree_nodes_json = request.GET.get('data', '[]')
        base_dir = request.GET.get('dir_path', None)
        dataset = Dataset.objects.get(id=dataset_id)
        if not (tree_nodes_json and base_dir):
            return HttpResponse('Please specify base directory', status=400)
        tree_nodes = json.loads(tree_nodes_json)

        # Previously this method checked the tree nodes data passed
        # in to determine whether children has already been loaded,
        # but now that logic will be moved to the front-end component.

        # list dir under base_dir
        child_dir_tuples = dataset.get_dir_tuples(
            request.user, basedir=base_dir)
        # list files under base_dir
        dfs = DataFile.safe.all(request.user).filter(
            dataset=dataset, directory=base_dir)
        # walk the directory tree and append files and dirs
        # if there are directories append this to data
        child_list = []
        if child_dir_tuples:
            child_list = dataset.get_dir_nodes(request.user, child_dir_tuples)

        # if there are files append this
        if dfs:
            filenames = [df.filename for df in dfs]
            for file_name in filenames:
                child = {'name': file_name}
                child_list.append(child)

        return JsonResponse(child_list, status=200, safe=False)

    def _populate_children(self, sub_child_dirs, dir_node, dataset):
        '''Populate the children list in a directory node
        Example dir_node: {'name': u'child_1', 'children': []}
        '''
        child_dir_list = []
        for dir in sub_child_dirs:
            part1, part2 = dir
            # get files for this dir
            dfs = DataFile.objects.filter(dataset=dataset, directory=part2)
            filenames = [df.filename for df in dfs]
            if part1 == '..':
                for file_name in filenames:
                    child = {'name': file_name}
                    dir_node['children'].append(child)
            else:
                children = []
                for file_name in filenames:
                    child = {'name': file_name}
                    children.append(child)
                dir_node['children'].append(
                    {'name': part2.rpartition('/')[2], 'children': children})


class DataFileResource(MyTardisModelResource):
    dataset = fields.ForeignKey(DatasetResource, 'dataset')
    parameter_sets = fields.ToManyField(
        'tardis.tardis_portal.api.DatafileParameterSetResource',
        'datafileparameterset_set',
        related_name='datafile',
        full=True, null=True)
    datafile = fields.FileField()
    replicas = fields.ToManyField(
        'tardis.tardis_portal.api.ReplicaResource',
        'file_objects',
        related_name='datafile', full=True, null=True)
    temp_url = None

    class Meta(MyTardisModelResource.Meta):
        object_class = DataFile
        queryset = DataFile.objects.all()
        filtering = {
            'id': ('exact', ),
            'directory': ('exact', 'startswith'),
            'dataset': ALL_WITH_RELATIONS,
            'filename': ('exact', ),
        }
        ordering = [
            'id',
            'filename',
            'modification_time'
        ]
        resource_name = 'dataset_file'
        always_return_data = True

    def dehydrate(self, bundle):
        datafile = bundle.obj
        admins = datafile.get_admins()
        logger.error(admins)
        bundle.data['admin_groups'] = [acl.id for acl in admins]
        members = datafile.get_groups()
        logger.error(members)
        bundle.data['member_groups'] = [acl.id for acl in members]
        return bundle

    def download_file(self, request, **kwargs):
        '''
        curl needs the -J switch to get the filename right
        auth needs to be added manually here
        '''
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        if not has_download_access(
                request=request, obj_id=kwargs['pk'], ct_type="datafile"):
            return HttpResponseForbidden()

        file_record = self._meta.queryset.get(pk=kwargs['pk'])
        self.authorized_read_detail(
            [file_record],
            self.build_bundle(obj=file_record, request=request))

        preferred_dfo = file_record.get_preferred_dfo()
        if not preferred_dfo:
            # No verified DataFileObject exists for this DataFile
            return HttpResponseNotFound()

        storage_class_name = preferred_dfo.storage_box.django_storage_class
        download_uri_templates = getattr(
            settings, 'DOWNLOAD_URI_TEMPLATES', {})
        if storage_class_name in download_uri_templates:
            template = URITemplate(download_uri_templates[storage_class_name])
            return redirect(template.expand(dfo_id=preferred_dfo.id))

        file_object = file_record.get_file()
        wrapper = FileWrapper(file_object)
        tracker_data = dict(
            label='file',
            session_id=request.COOKIES.get('_ga'),
            ip=request.META.get('REMOTE_ADDR', ''),
            user=request.user,
            total_size=file_record.size,
            num_files=1,
            ua=request.META.get('HTTP_USER_AGENT', None))
        response = StreamingHttpResponse(
            IteratorTracker(wrapper, tracker_data),
            content_type=file_record.mimetype)
        response['Content-Length'] = file_record.size
        response['Content-Disposition'] = 'attachment; filename="%s"' % \
                                          file_record.filename
        self.log_throttled_access(request)
        return response

    def verify_file(self, request, **kwargs):
        '''triggers verification of file, e.g. after non-POST upload complete
        '''
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        if not has_download_access(
                request=request, obj_id=kwargs['pk'], ct_type="datafile"):
            return HttpResponseForbidden()

        file_record = self._meta.queryset.get(pk=kwargs['pk'])
        self.authorized_read_detail(
            [file_record],
            self.build_bundle(obj=file_record, request=request))
        for dfo in file_record.file_objects.all():
            shadow = 'dfo_verify location:%s' % dfo.storage_box.name
            tasks.dfo_verify.apply_async(
                args=[dfo.id],
                priority=dfo.priority,
                shadow=shadow)
        return HttpResponse()

    def hydrate(self, bundle):
        if 'attached_file' in bundle.data:
            # have POSTed file
            newfile = bundle.data['attached_file'][0]
            compute_md5 = getattr(settings, 'COMPUTE_MD5', True)
            compute_sha512 = getattr(settings, 'COMPUTE_SHA512', False)
            if (compute_md5 and 'md5sum' not in bundle.data) or \
                    (compute_sha512 and 'sha512sum' not in bundle.data):
                checksums = compute_checksums(
                    newfile,
                    compute_md5=compute_md5,
                    compute_sha512=compute_sha512,
                    close_file=False)
                if compute_md5:
                    bundle.data['md5sum'] = checksums['md5sum']
                if compute_sha512:
                    bundle.data['sha512sum'] = checksums['sha512sum']

            if 'replicas' in bundle.data:
                for replica in bundle.data['replicas']:
                    replica.update({'file_object': newfile})
            else:
                bundle.data['replicas'] = [{'file_object': newfile}]

            del(bundle.data['attached_file'])
        return bundle

    @transaction.atomic
    def obj_create(self, bundle, **kwargs):
        '''
        Creates a new DataFile object from the provided bundle.data dict.
        If a duplicate key error occurs, responds with HTTP Error 409: CONFLICT
        '''
        logger.error('Building datafile in obj_create')
        admin_groups = None
        member_groups = None
        admins = None
        members = None
        if 'admin_groups' in bundle.data.keys():
            admin_groups = bundle.data.pop('admin_groups')
        if 'member_groups' in bundle.data.keys():
            member_groups = bundle.data.pop('member_groups')
        if 'admins' in bundle.data.keys():
            admins = bundle.data.pop('admins')
        if 'members' in bundle.data.keys():
            members = bundle.data.pop('members')
        try:
            retval = super().obj_create(bundle, **kwargs)
        except IntegrityError as err:
            if "duplicate key" in str(err):
                raise ImmediateHttpResponse(HttpResponse(status=409))
            raise
        if 'replicas' not in bundle.data or not bundle.data['replicas']:
            # no replica specified: return upload path and create dfo for
            # new path
            sbox = bundle.obj.get_receiving_storage_box()
            if sbox is None:
                raise NotImplementedError
            dfo = DataFileObject(
                datafile=bundle.obj,
                storage_box=sbox)
            dfo.create_set_uri()
            dfo.save()
            self.temp_url = dfo.get_full_path()
        datafile = retval.obj
        try:
            dataset_uri = retval.data['dataset']
            dataset = DatasetResource.get_via_uri(
                DatasetResource(), dataset_uri, bundle.request)
        except NotFound:
            logger.error(
                "Unable to locate parent dataset for {}".format(retval.data["filename"]))
            raise
        logger.error(dataset)
        experiment = dataset.experiments.all()[0]
        logger.error('Experiment')
        logger.error(experiment)
        project = experiment.project
        project_lead = project.lead_researcher
        logger.error('Lead Researcher')
        logger.error(project_lead)
        logger.error(project_lead.id)
        logger.error('Content Type')
        logger.error(datafile.get_ct())
        logger.error(datafile.id)
        datafile_admin_groups = []
        datafile_groups = []
        datafile_admin_users = []
        # TODO: unify this with the view function's ACL creation,
        # maybe through an ACL toolbox.
        acl = ObjectACL(content_type=datafile.get_ct(),
                        object_id=datafile.id,
                        pluginId=django_user,
                        entityId=str(project_lead.id),
                        canRead=True,
                        canDownload=True,
                        canWrite=True,
                        canDelete=True,
                        canSensitive=True,
                        isOwner=True,
                        aclOwnershipType=ObjectACL.OWNER_OWNED)
        acl.save()
        if not admin_groups:
            admin_groups = dataset.get_admins()
        if admin_groups != []:
            for grp in admin_groups:
                group, created = Group.objects.get_or_create(name=grp)
                datafile_admin_groups.append(group)
                datafile_groups.append(group)
                if created:
                    group.permissions.set(admin_perms)
                    create_acl(datafile.get_ct(),
                               datafile.id,
                               django_group,
                               group.id,
                               admin=True)
                if group not in Project.safe.groups(project.id):
                    create_acl(project.get_ct(),
                               project.id,
                               django_group,
                               group.id)
                if group not in Experiment.safe.groups(experiment.id):
                    create_acl(experiment.get_ct(),
                               experiment.id,
                               django_group,
                               group.id)
                if group not in Dataset.safe.groups(dataset.id):
                    create_acl(dataset.get_ct(),
                               dataset.id,
                               django_group,
                               group.id)
        if not member_groups:
            member_groups = dataset.get_groups_and_perms()
            # Each member group is defined by a tuple
            # (group_name, sensitive[T/F], download[T/F])
            # unpack for ACLs
            logger.error("Groups to append: {}".format(member_groups))
        if member_groups != []:
            for grp in member_groups:
                grp_name = grp[0]
                sensitive_flg = grp[1]
                download_flg = grp[2]
                group, created = Group.objects.get_or_create(name=grp_name)
                datafile_groups.append(group)
                if created:
                    group.permissions.set(member_perms)
                create_acl(datafile.get_ct(),
                           datafile.id,
                           django_group,
                           group.id,
                           write=True,
                           download=download_flg,
                           sensitive=sensitive_flg,
                           admin=False)
                if group not in Project.safe.groups(project.id):
                    create_acl(project.get_ct(),
                               project.id,
                               django_group,
                               group.id)
                if group not in Experiment.safe.groups(experiment.id):
                    create_acl(experiment.get_ct(),
                               experiment.id,
                               django_group,
                               group.id)
                if group not in Dataset.safe.groups(dataset.id):
                    create_acl(dataset.get_ct(),
                               dataset.id,
                               django_group,
                               group.id)
        if not admins:
            # Cascade the admin from the project level
            dataset_admins = dataset.get_owners()
            for user in dataset_admins:
                if user.username == project.lead_researcher:
                    # Lead researchers get all perms
                    continue
                add_flg = True
                if members:
                    for member in members:
                        if user.username == member[0]:
                            # Don't add this user to the admin group since they have implicitly
                            # been downgraded
                            add_flg = False
                        if add_flg:
                            create_acl(datafile.get_ct(),
                                       datafile.id,
                                       django_user,
                                       user.id,
                                       admin=True)
                # No need to check traverse since they have admin rights in parent
        elif admins != []:
            for admin in admins:
                if not User.objects.filter(username=admin).exists():
                    new_user = get_user_from_upi(admin)
                    user = User.objects.create(username=new_user['username'],
                                               first_name=new_user['first_name'],
                                               last_name=new_user['last_name'],
                                               email=new_user['email'])
                    user.set_password(gen_random_password())
                    for permission in admin_perms:
                        user.user_permissions.add(permission)
                    user.save()
                    authentication = UserAuthentication(userProfile=user.userprofile,
                                                        username=new_user['username'],
                                                        authenticationMethod=settings.LDAP_METHOD)
                    authentication.save()
                user = User.objects.get(username=admin)
                datafile_admin_users.append(user)
                create_acl(datafile.get_ct(),
                           datafile.id,
                           django_user,
                           user.id,
                           admin=True)
                if user not in Project.safe.users(project.id):
                    create_acl(project.get_ct(),
                               project.id,
                               django_user,
                               user.id)
                if user not in Experiment.safe.users(experiment.id):
                    create_acl(experiment.get_ct(),
                               experiment.id,
                               django_user,
                               user.id)
                if user not in Dataset.safe.users(dataset.id):
                    create_acl(dataset.get_ct(),
                               dataset.id,
                               django_user,
                               user.id)

        # error checking needs to be done externally for this to
        # function as desired.
        if not members:
            dataset_members = dataset.get_users_and_perms()
            for user_tuple in dataset_members:
                user, sensitive, download = user_tuple
                if user.username == project.lead_researcher:
                    # Lead researchers get all perms
                    continue
                create_acl(datafile.get_ct(),
                           datafile.id,
                           django_user,
                           user.id,
                           write=True,
                           download=download,
                           sensitive=sensitive,
                           admin=False)
        elif members != []:
            members = bundle.data['members']
            for member in members:
                member_name = member[0]
                sensitive_flg = member[1]
                download_flg = member[2]
                if not User.objects.filter(username=member_name).exists():
                    new_user = get_user_from_upi(member_name)
                    if not new_user:
                        logger.error(
                            "No one found for upi: {}".format(member_name))
                    user = User.objects.create(username=new_user['username'],
                                               first_name=new_user['first_name'],
                                               last_name=new_user['last_name'],
                                               email=new_user['email'])
                    user.set_password(gen_random_password())
                    for permission in member_perms:
                        user.user_permissions.add(permission)
                    user.save()
                    authentication = UserAuthentication(userProfile=user.userprofile,
                                                        username=new_user['username'],
                                                        authenticationMethod=settings.LDAP_METHOD)
                    authentication.save()
                user = User.objects.get(username=member_name)
                create_acl(datafile.get_ct(),
                           datafile.id,
                           django_user,
                           user.id,
                           write=True,
                           download=download_flg,
                           sensitive=sensitive_flg,
                           admin=False)
                if user not in Project.safe.users(project.id):
                    create_acl(project.get_ct(),
                               project.id,
                               django_user,
                               user.id)
                if user not in Experiment.safe.users(project.id):
                    create_acl(experiment.get_ct(),
                               experiment.id,
                               django_user,
                               user.id)
                if user not in Dataset.safe.users(dataset.id):
                    create_acl(dataset.get_ct(),
                               dataset.id,
                               django_user,
                               user.id)

        for group in datafile_groups:
            logger.error("Creating group admin for {}".format(group))
            group_admin, _ = GroupAdmin.objects.get_or_create(user=bundle.request.user,
                                                              group=group)
            for admin in datafile_admin_groups:
                group_admin.admin_groups.add(admin.id)
            for admin in datafile_admin_users:
                group_admin.admin_users.add(admin.id)
            logger.error(group_admin)
        return retval

    def post_list(self, request, **kwargs):
        response = super().post_list(request, **kwargs)
        if self.temp_url is not None:
            response.content = self.temp_url
            self.temp_url = None
        return response

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/download%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('download_file'), name="api_download_file"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/verify%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('verify_file'), name="api_verify_file"),
        ]

    def deserialize(self, request, data, format=None):
        '''
        from https://github.com/toastdriven/django-tastypie/issues/42
        modified to deserialize json sent via POST. Would fail if data is sent
        in a different format.
        uses a hack to get back pure json from request.POST
        '''
        if not format:
            format = request.META.get('CONTENT_TYPE', 'application/json')
        if format == 'application/x-www-form-urlencoded':
            return request.POST
        if format.startswith('multipart'):
            jsondata = request.POST['json_data']
            data = json.loads(jsondata)
            data.update(request.FILES)
            return data
        return super().deserialize(request, data, format)

    def put_detail(self, request, **kwargs):
        '''
        from https://github.com/toastdriven/django-tastypie/issues/42
        '''
        if request.META.get('CONTENT_TYPE').startswith('multipart') and \
                not hasattr(request, '_body'):
            request._body = ''

        return super().put_detail(request, **kwargs)


class SchemaResource(MyTardisModelResource):

    class Meta(MyTardisModelResource.Meta):
        object_class = Schema
        queryset = Schema.objects.all()
        filtering = {
            'id': ('exact', ),
            'namespace': ('exact', ),
        }
        ordering = [
            'id'
        ]


class ParameterNameResource(MyTardisModelResource):
    schema = fields.ForeignKey(SchemaResource, 'schema')

    class Meta(MyTardisModelResource.Meta):
        object_class = ParameterName
        queryset = ParameterName.objects.all()
        filtering = {
            'schema': ALL_WITH_RELATIONS,
        }


class ParameterResource(MyTardisModelResource):
    name = fields.ForeignKey(ParameterNameResource, 'name')
    value = fields.CharField(blank=True)

    def hydrate(self, bundle):
        '''
        sets the parametername by uri or name
        if untyped value is given, set value via parameter method,
        otherwise use modelresource automatisms
        '''
        try:
            parname = ParameterNameResource.get_via_uri(
                ParameterNameResource(),
                bundle.data['name'], bundle.request)
        except NotFound:
            parname = bundle.related_obj._get_create_parname(
                bundle.data['name'])
        del(bundle.data['name'])
        bundle.obj.name = parname
        if 'value' in bundle.data:
            bundle.obj.set_value(bundle.data['value'])
            del(bundle.data['value'])
        return bundle


class ParameterSetResource(MyTardisModelResource):
    schema = fields.ForeignKey(SchemaResource, 'schema', full=True)

    def hydrate_schema(self, bundle):
        try:
            schema = SchemaResource.get_via_uri(SchemaResource(),
                                                bundle.data['schema'],
                                                bundle.request)
            logger.error(schema)
        except NotFound:
            schema = Schema.objects.get(namespace=bundle.data['schema'])
        bundle.obj.schema = schema
        del(bundle.data['schema'])
        return bundle


class DatafileParameterSetResource(ParameterSetResource):
    datafile = fields.ForeignKey(
        DataFileResource, 'datafile')
    parameters = fields.ToManyField(
        'tardis.tardis_portal.api.DatafileParameterResource',
        'datafileparameter_set',
        related_name='parameterset', full=True, null=True)

    class Meta(ParameterSetResource.Meta):
        object_class = DatafileParameterSet
        queryset = DatafileParameterSet.objects.all()


class DatafileParameterResource(ParameterResource):
    parameterset = fields.ForeignKey(DatafileParameterSetResource,
                                     'parameterset')

    class Meta(ParameterResource.Meta):
        object_class = DatafileParameter
        queryset = DatafileParameter.objects.all()


class LocationResource(MyTardisModelResource):
    class Meta(MyTardisModelResource.Meta):
        queryset = StorageBox.objects.all()


class ReplicaResource(MyTardisModelResource):
    datafile = fields.ForeignKey(DataFileResource, 'datafile')

    class Meta(MyTardisModelResource.Meta):
        object_class = DataFileObject
        queryset = DataFileObject.objects.all()
        filtering = {
            'verified': ('exact',),
            'url': ('exact', 'startswith'),
        }
        ordering = [
            'id'
        ]

    def hydrate(self, bundle):
        if 'url' in bundle.data:
            if 'file_object' not in bundle.data:
                bundle.data['uri'] = bundle.data['url']
            del(bundle.data['url'])
        datafile = bundle.related_obj
        bundle.obj.datafile = datafile
        bundle.data['datafile'] = datafile
        if 'location' in bundle.data:
            try:
                bundle.obj.storage_box = StorageBox.objects.get(
                    name=bundle.data['location'])
            except StorageBox.DoesNotExist:
                bundle.obj.storage_box = datafile.get_default_storage_box()
            del(bundle.data['location'])
        else:
            bundle.obj.storage_box = datafile.get_default_storage_box()

        bundle.obj.save()
        if 'file_object' in bundle.data:
            bundle.obj.file_object = bundle.data['file_object']
            bundle.data['file_object'].close()
            del(bundle.data['file_object'])
            bundle.obj = DataFileObject.objects.get(id=bundle.obj.id)
        return bundle

    def dehydrate(self, bundle):
        dfo = bundle.obj
        bundle.data['location'] = dfo.storage_box.name
        return bundle


class ObjectACLResource(MyTardisModelResource):
    content_object = GenericForeignKeyField({
        Experiment: ExperimentResource,
        Dataset: DatasetResource,
        DataFile: DataFileResource,
        Project: ProjectResource
        # ...
    }, 'content_object')

    class Meta:
        object_class = ObjectACL
        authentication = default_authentication
        authorization = ACLAuthorization()
        queryset = ObjectACL.objects.all()
        filtering = {
            'pluginId': ('exact', ),
            'entityId': ('exact', ),
        }
        ordering = [
            'id'
        ]

    def hydrate(self, bundle):
        # Fill in the content type.
        if bundle.data['content_type'] == 'project':
            project = Project.objects.get(pk=bundle.data['object_id'])
            bundle.obj.content_type = project.get_ct()
        if bundle.data['content_type'] == 'experiment':
            experiment = Experiment.objects.get(pk=bundle.data['object_id'])
            bundle.obj.content_type = experiment.get_ct()
        elif bundle.data['content_type'] == 'dataset':
            dataset = Dataset.objects.get(pk=bundle.data['object_id'])
            bundle.obj.content_type = dataset.get_ct()
        elif bundle.data['content_type'] == 'datafile':
            datafile = DataFile.objects.get(pk=bundle.data['object_id'])
            bundle.obj.content_type = datafile.get_ct()
        else:
            raise NotImplementedError(str(bundle.obj))
        return bundle


class ExperimentParameterSetResource(ParameterSetResource):
    '''API for ExperimentParameterSets
    '''
    experiment = fields.ForeignKey(ExperimentResource, 'experiment')
    parameters = fields.ToManyField(
        'tardis.tardis_portal.api.ExperimentParameterResource',
        'experimentparameter_set',
        related_name='parameterset', full=True, null=True)

    class Meta(ParameterSetResource.Meta):
        object_class = ExperimentParameterSet
        queryset = ExperimentParameterSet.objects.all()


class ExperimentParameterResource(ParameterResource):
    parameterset = fields.ForeignKey(ExperimentParameterSetResource,
                                     'parameterset')

    class Meta(ParameterResource.Meta):
        object_class = ExperimentParameter
        queryset = ExperimentParameter.objects.all()


class ProjectParameterSetResource(ParameterSetResource):
    '''API for ExperimentParameterSets
    '''
    project = fields.ForeignKey(ProjectResource, 'project')
    parameters = fields.ToManyField(
        'tardis.tardis_portal.api.ProjectParameterResource',
        'projectparameter_set',
        related_name='parameterset', full=True, null=True)

    class Meta(ParameterSetResource.Meta):
        object_class = ProjectParameterSet
        queryset = ProjectParameterSet.objects.all()


class ProjectParameterResource(ParameterResource):
    parameterset = fields.ForeignKey(ProjectParameterSetResource,
                                     'parameterset')

    class Meta(ParameterResource.Meta):
        object_class = ProjectParameter
        queryset = ProjectParameter.objects.all()


class DatasetParameterSetResource(ParameterSetResource):
    dataset = fields.ForeignKey(DatasetResource, 'dataset')
    parameters = fields.ToManyField(
        'tardis.tardis_portal.api.DatasetParameterResource',
        'datasetparameter_set',
        related_name='parameterset', full=True, null=True)

    class Meta(ParameterSetResource.Meta):
        object_class = DatasetParameterSet
        queryset = DatasetParameterSet.objects.all()


class DatasetParameterResource(ParameterResource):
    parameterset = fields.ForeignKey(DatasetParameterSetResource,
                                     'parameterset')

    class Meta(ParameterResource.Meta):
        object_class = DatasetParameter
        queryset = DatasetParameter.objects.all()


class StorageBoxResource(MyTardisModelResource):
    options = fields.ToManyField(
        'tardis.tardis_portal.api.StorageBoxOptionResource',
        attribute=lambda bundle: StorageBoxOption.objects
        .filter(storage_box=bundle.obj,
                key__in=StorageBoxOptionResource.accessible_keys),
        related_name='storage_box',
        full=True, null=True)
    attributes = fields.ToManyField(
        'tardis.tardis_portal.api.StorageBoxAttributeResource',
        'attributes',
        related_name='storage_box',
        full=True, null=True)

    class Meta(MyTardisModelResource.Meta):
        object_class = StorageBox
        queryset = StorageBox.objects.all()
        ordering = [
            'id'
        ]


class StorageBoxOptionResource(MyTardisModelResource):
    accessible_keys = ['location']
    storage_box = fields.ForeignKey(
        StorageBoxResource,
        'storage_box',
        related_name='options',
        full=False)

    class Meta(MyTardisModelResource.Meta):
        object_class = StorageBoxOption
        queryset = StorageBoxOption.objects.all()
        ordering = [
            'id'
        ]


class StorageBoxAttributeResource(MyTardisModelResource):
    storage_box = fields.ForeignKey(
        StorageBoxResource,
        'storage_box',
        related_name='attributes',
        full=False)

    class Meta(MyTardisModelResource.Meta):
        object_class = StorageBoxAttribute
        queryset = StorageBoxAttribute.objects.all()
        ordering = [
            'id'
        ]
