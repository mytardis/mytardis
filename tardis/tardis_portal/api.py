# pylint: disable=C0302
"""
RESTful API for MyTardis models and data.
Implemented with Tastypie.

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
"""
import json
import re
from wsgiref.util import FileWrapper
from itertools import chain

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    StreamingHttpResponse,
    HttpResponseNotFound,
    JsonResponse,
)
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
from tastypie.resources import Resource, ModelResource, Bundle
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash

from uritemplate import URITemplate

import ldap3

from tardis.analytics.tracker import IteratorTracker
from . import tasks
from .auth.decorators import (
    has_access,
    has_download_access,
    has_sensitive_access,
    has_write,
    has_delete_permissions,
)
from .models.access_control import (
    ExperimentACL,
    DatasetACL,
    DatafileACL,
    UserAuthentication,
)
from .models.datafile import DataFile, DataFileObject, compute_checksums
from .models.dataset import Dataset
from .models.experiment import Experiment, ExperimentAuthor
from .models.parameters import (
    DatafileParameter,
    DatafileParameterSet,
    DatasetParameter,
    DatasetParameterSet,
    ExperimentParameter,
    ExperimentParameterSet,
    ParameterName,
    Schema,
)
from .models.storage import StorageBox, StorageBoxOption, StorageBoxAttribute
from .models.facility import Facility, facilities_managed_by
from .models.instrument import Instrument


class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return (
            json.dumps(
                data,
                cls=json.JSONEncoder,
                sort_keys=True,
                ensure_ascii=False,
                indent=self.json_indent,
            )
            + "\n"
        )


if settings.DEBUG:
    default_serializer = PrettyJSONSerializer()
else:
    default_serializer = Serializer()


def get_user_from_upi(upi):
    server = ldap3.Server(settings.LDAP_URL)
    search_filter = "({}={})".format(settings.LDAP_USER_LOGIN_ATTR, upi)
    with ldap3.Connection(
        server,
        auto_bind=True,
        user=settings.LDAP_ADMIN_USER,
        password=settings.LDAP_ADMIN_PASSWORD,
    ) as connection:
        connection.search(settings.LDAP_USER_BASE, search_filter, attributes=["*"])
        if len(connection.entries) > 1:
            error_message = (
                "More than one person with {}: {} has been found in the LDAP".format(
                    settings.LDAP_USER_LOGIN_ATTR, upi
                )
            )
            # if logger:
            #    logger.error(error_message)
            raise Exception(error_message)
        if len(connection.entries) == 0:
            error_message = "No one with {}: {} has been found in the LDAP".format(
                settings.LDAP_USER_LOGIN_ATTR, upi
            )
            # if logger:
            #    logger.warning(error_message)
            return None
        person = connection.entries[0]
        first_name_key = "givenName"
        last_name_key = "sn"
        email_key = "mail"
        username = person[settings.LDAP_USER_LOGIN_ATTR].value
        first_name = person[first_name_key].value
        last_name = person[last_name_key].value
        try:
            email = person[email_key].value
        except KeyError:
            email = ""
        details = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }
        return details


def gen_random_password():
    import random

    random.seed()
    characters = "abcdefghijklmnopqrstuvwxyzABCDFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
    passlen = 16
    password = "".join(random.sample(characters, passlen))
    return password


def get_or_create_user(username):
    if not User.objects.filter(username=username).exists():
        new_user = get_user_from_upi(username)
        user = User.objects.create(
            username=new_user["username"],
            first_name=new_user["first_name"],
            last_name=new_user["last_name"],
            email=new_user["email"],
        )
        user.set_password(gen_random_password())
        user.save()
        authentication = UserAuthentication(
            userProfile=user.userprofile,
            username=new_user["username"],
            authenticationMethod=settings.LDAP_METHOD,
        )
        authentication.save()
    else:
        user = User.objects.get(username=username)
    return user


class MyTardisAuthentication(object):
    """
    custom tastypie authentication that works with both anonymous use and
    a number of available auth mechanisms.
    """

    def is_authenticated(self, request, **kwargs):  # noqa # too complex
        """
        handles backends explicitly so that it can return False when
        credentials are given but wrong and return Anonymous User when
        credentials are not given or the session has expired (web use).
        """
        auth_info = request.META.get("HTTP_AUTHORIZATION")

        if "HTTP_AUTHORIZATION" not in request.META:
            if hasattr(request.user, "allowed_tokens"):
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
        if auth_info.startswith("Basic"):
            basic_auth = BasicAuthentication()
            check = basic_auth.is_authenticated(request, **kwargs)
            if check:
                if isinstance(check, HttpUnauthorized):
                    return False
                request._authentication_backend = basic_auth
                return check
        if auth_info.startswith("ApiKey"):
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
            return "nouser"


default_authentication = MyTardisAuthentication()


class ACLAuthorization(Authorization):
    """Authorisation class for Tastypie."""

    def read_list(self, object_list, bundle):  # noqa # too complex
        obj_ids = [obj.id for obj in object_list]
        if bundle.request.user.is_authenticated and bundle.request.user.is_superuser:
            return object_list
        if isinstance(bundle.obj, Experiment):
            experiments = Experiment.safe.all(bundle.request.user)
            return experiments.filter(id__in=obj_ids)
        if isinstance(bundle.obj, ExperimentAuthor):
            experiments = Experiment.safe.all(bundle.request.user)
            return ExperimentAuthor.objects.filter(
                experiment__in=experiments, id__in=obj_ids
            )
        if isinstance(bundle.obj, ExperimentParameterSet):
            experiments = Experiment.safe.all(bundle.request.user)
            return ExperimentParameterSet.objects.filter(
                experiment__in=experiments, id__in=obj_ids
            )
        if isinstance(bundle.obj, ExperimentParameter):
            experiments = Experiment.safe.all(bundle.request.user)
            exp_params = ExperimentParameter.objects.filter(
                parameterset__experiment__in=experiments, id__in=obj_ids
            )
            # Generator to filter sensitive exp_parameters when given an exp id
            def get_exp_param(exp_par):
                if not exp_par.name.sensitive:
                    yield exp_par
                elif has_sensitive_access(
                    bundle.request, exp_par.parameterset.experiment.id, "experiment"
                ):
                    yield exp_par

            # Take chained generators and turn them into a set of parameters
            return list(chain(chain.from_iterable(map(get_exp_param, exp_params))))
        if isinstance(bundle.obj, Dataset):
            dataset_ids = [
                ds.id
                for ds in object_list
                if has_access(bundle.request, ds.id, "dataset")
            ]
            return Dataset.objects.filter(id__in=dataset_ids)
        if isinstance(bundle.obj, DatasetParameterSet):
            return [
                dps
                for dps in object_list
                if has_access(bundle.request, dps.dataset.id, "dataset")
            ]
        if isinstance(bundle.obj, DatasetParameter):
            dp_list = [
                dp
                for dp in object_list
                if has_access(bundle.request, dp.parameterset.dataset.id, "dataset")
            ]
            # Generator to filter sensitive exp_parameters when given an exp id
            def get_set_param(set_par):
                if not set_par.name.sensitive:
                    yield set_par
                elif has_sensitive_access(
                    bundle.request, set_par.parameterset.dataset.id, "dataset"
                ):
                    yield set_par

            # Take chained generators and turn them into a set of parameters
            return list(chain(chain.from_iterable(map(get_set_param, dp_list))))
        if isinstance(bundle.obj, DataFile):
            datafile_ids = [
                df.id
                for df in object_list
                if has_access(bundle.request, df.id, "datafile")
            ]
            return DataFile.objects.filter(id__in=datafile_ids)
        if isinstance(bundle.obj, DatafileParameterSet):
            return [
                dps
                for dps in object_list
                if has_access(bundle.request, dps.datafile.id, "datafile")
            ]
        if isinstance(bundle.obj, DatafileParameter):
            dp_list = [
                dp
                for dp in object_list
                if has_access(bundle.request, dp.parameterset.datafile.id, "datafile")
            ]
            # Generator to filter sensitive exp_parameters when given an exp id
            def get_file_param(file_par):
                if not file_par.name.sensitive:
                    yield file_par
                elif has_sensitive_access(
                    bundle.request, file_par.parameterset.datafile.id, "datafile"
                ):
                    yield file_par

            # Take chained generators and turn them into a set of parameters
            return list(chain(chain.from_iterable(map(get_file_param, dp_list))))
        if isinstance(bundle.obj, Schema):
            return object_list
        if isinstance(bundle.obj, ParameterName):
            return object_list
        if isinstance(bundle.obj, ExperimentACL):
            query = ExperimentACL.objects.none()
            if bundle.request.user.is_authenticated:
                query |= bundle.request.user.experimentacls.all()
                for group in bundle.request.user.groups.all():
                    query |= group.experimentacls.all()
            return query
        if isinstance(bundle.obj, DatasetACL):
            query = DatasetACL.objects.none()
            if bundle.request.user.is_authenticated:
                query |= bundle.request.user.datasetacls.all()
                for group in bundle.request.user.groups.all():
                    query |= group.datasetacls.all()
            return query
        if isinstance(bundle.obj, DatafileACL):
            query = DatafileACL.objects.none()
            if bundle.request.user.is_authenticated:
                query |= bundle.request.user.datafileacls.all()
                for group in bundle.request.user.groups.all():
                    query |= group.datafileacls.all()
            return query
        if bundle.request.user.is_authenticated and isinstance(bundle.obj, User):
            if facilities_managed_by(bundle.request.user):
                return object_list
            return [
                user
                for user in object_list
                if (
                    user == bundle.request.user
                    or user.experiment_set.filter(public_access__gt=1).count() > 0
                )
            ]
        if isinstance(bundle.obj, Group):
            if facilities_managed_by(bundle.request.user).count() > 0:
                return object_list
            return bundle.request.user.groups.filter(id__in=obj_ids)
        if isinstance(bundle.obj, Facility):
            facilities = facilities_managed_by(bundle.request.user)
            return [facility for facility in object_list if facility in facilities]
        if isinstance(bundle.obj, Instrument):
            if bundle.request.user.is_authenticated:
                return object_list
        if isinstance(bundle.obj, StorageBox):
            if bundle.request.user.is_authenticated:
                return object_list
        if isinstance(bundle.obj, StorageBoxOption):
            if bundle.request.user.is_authenticated:
                return [
                    option
                    for option in object_list
                    if option.key in StorageBoxOptionResource.accessible_keys
                ]
        if isinstance(bundle.obj, StorageBoxAttribute):
            if bundle.request.user.is_authenticated:
                return object_list
        return []

    def read_detail(self, object_list, bundle):  # noqa # too complex
        if bundle.request.user.is_authenticated and bundle.request.user.is_superuser:
            return True
        if re.match("^/api/v1/[a-z_]+/schema/$", bundle.request.path):
            return True
        if isinstance(bundle.obj, Experiment):
            return has_access(bundle.request, bundle.obj.id, "experiment")
        if isinstance(bundle.obj, ExperimentAuthor):
            return has_access(bundle.request, bundle.obj.experiment.id, "experiment")
        if isinstance(bundle.obj, ExperimentParameterSet):
            return has_access(bundle.request, bundle.obj.experiment.id, "experiment")
        if isinstance(bundle.obj, ExperimentParameter):
            if bundle.obj.name.sensitive:
                return has_sensitive_access(
                    bundle.request, bundle.obj.parameterset.experiment.id, "experiment"
                )
            return has_access(
                bundle.request, bundle.obj.parameterset.experiment.id, "experiment"
            )
        if isinstance(bundle.obj, Dataset):
            return has_access(bundle.request, bundle.obj.id, "dataset")
        if isinstance(bundle.obj, DatasetParameterSet):
            return has_access(bundle.request, bundle.obj.dataset.id, "dataset")
        if isinstance(bundle.obj, DatasetParameter):
            if bundle.obj.name.sensitive:
                return has_sensitive_access(
                    bundle.request, bundle.obj.parameterset.dataset.id, "dataset"
                )
            return has_access(
                bundle.request, bundle.obj.parameterset.dataset.id, "dataset"
            )
        if isinstance(bundle.obj, DataFile):
            return has_access(bundle.request, bundle.obj.id, "datafile")
        if isinstance(bundle.obj, DatafileParameterSet):
            return has_access(bundle.request, bundle.obj.datafile.id, "datafile")
        if isinstance(bundle.obj, DatafileParameter):
            if bundle.obj.name.sensitive:
                return has_sensitive_access(
                    bundle.request, bundle.obj.parameterset.datafile.id, "datafile"
                )
            return has_access(
                bundle.request, bundle.obj.parameterset.datafile.id, "datafile"
            )
        if isinstance(bundle.obj, User):
            # allow all authenticated users to read public user info
            # the dehydrate function also adds/removes some information
            authenticated = bundle.request.user.is_authenticated
            public_user = (
                bundle.obj.experiment_set.filter(public_access__gt=1).count() > 0
            )
            return public_user or authenticated
        if isinstance(bundle.obj, Schema):
            return True
        if isinstance(bundle.obj, ParameterName):
            return True
        if isinstance(bundle.obj, StorageBox):
            return bundle.request.user.is_authenticated
        if isinstance(bundle.obj, StorageBoxOption):
            return (
                bundle.request.user.is_authenticated
                and bundle.obj.key in StorageBoxOptionResource.accessible_keys
            )
        if isinstance(bundle.obj, StorageBoxAttribute):
            return bundle.request.user.is_authenticated
        if isinstance(bundle.obj, Group):
            return bundle.obj in bundle.request.user.groups.all()
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
        if bundle.request.user.is_authenticated and bundle.request.user.is_superuser:
            return True
        if isinstance(bundle.obj, Experiment):
            return bundle.request.user.has_perm("tardis_portal.add_experiment")
        if isinstance(bundle.obj, ExperimentAuthor):
            return bundle.request.user.has_perm("tardis_portal.add_experiment")
        if isinstance(bundle.obj, ExperimentParameterSet):
            if not bundle.request.user.has_perm("tardis_portal.change_experiment"):
                return False
            experiment_uri = bundle.data.get("experiment", None)
            if experiment_uri is not None:
                experiment = ExperimentResource.get_via_uri(
                    ExperimentResource(), experiment_uri, bundle.request
                )
                return has_write(bundle.request, experiment.id, "experiment")
            if getattr(bundle.obj.experiment, "id", False):
                return has_write(bundle.request, bundle.obj.experiment.id, "experiment")
            return False
        if isinstance(bundle.obj, ExperimentParameter):
            return bundle.request.user.has_perm(
                "tardis_portal.change_experiment"
            ) and has_write(
                bundle.request, bundle.obj.parameterset.experiment.id, "experiment"
            )
        if isinstance(bundle.obj, Dataset):
            if not bundle.request.user.has_perm("tardis_portal.change_dataset"):
                return False
            perm = False
            for exp_uri in bundle.data.get("experiments", []):
                try:
                    this_exp = ExperimentResource.get_via_uri(
                        ExperimentResource(), exp_uri, bundle.request
                    )
                except:
                    return False
                if has_write(bundle.request, this_exp.id, "experiment"):
                    perm = True
                else:
                    return False
            return perm
        if isinstance(bundle.obj, DatasetParameterSet):
            if not bundle.request.user.has_perm("tardis_portal.change_dataset"):
                return False
            dataset_uri = bundle.data.get("dataset", None)
            if dataset_uri is not None:
                dataset = DatasetResource.get_via_uri(
                    DatasetResource(), dataset_uri, bundle.request
                )
                return has_write(bundle.request, dataset.id, "dataset")
            if getattr(bundle.obj.dataset, "id", False):
                return has_write(bundle.request, bundle.obj.dataset.id, "dataset")
            return False
        if isinstance(bundle.obj, DatasetParameter):
            return bundle.request.user.has_perm(
                "tardis_portal.change_dataset"
            ) and has_write(
                bundle.request, bundle.obj.parameterset.dataset.id, "dataset"
            )
        if isinstance(bundle.obj, DataFile):
            dataset = DatasetResource.get_via_uri(
                DatasetResource(), bundle.data["dataset"], bundle.request
            )
            return all(
                [
                    bundle.request.user.has_perm("tardis_portal.change_dataset"),
                    bundle.request.user.has_perm("tardis_portal.add_datafile"),
                    has_write(bundle.request, dataset.id, "dataset"),
                ]
            )
        if isinstance(bundle.obj, DatafileParameterSet):
            dataset = Dataset.objects.get(pk=bundle.obj.datafile.dataset.id)
            return all(
                [
                    bundle.request.user.has_perm("tardis_portal.change_dataset"),
                    bundle.request.user.has_perm("tardis_portal.add_datafile"),
                    has_write(bundle.request, dataset.id, "dataset"),
                ]
            )
        if isinstance(bundle.obj, DatafileParameter):
            dataset = Dataset.objects.get(
                pk=bundle.obj.parameterset.datafile.dataset.id
            )
            return all(
                [
                    bundle.request.user.has_perm("tardis_portal.change_dataset"),
                    bundle.request.user.has_perm("tardis_portal.add_datafile"),
                    has_write(bundle.request, dataset.id, "dataset"),
                ]
            )
        if isinstance(bundle.obj, DataFileObject):
            return all(
                [
                    bundle.request.user.has_perm("tardis_portal.change_dataset"),
                    bundle.request.user.has_perm("tardis_portal.add_datafile"),
                    has_write(
                        bundle.request, bundle.obj.datafile.dataset.id, "dataset"
                    ),
                ]
            )
        if isinstance(bundle.obj, ExperimentACL):
            return bundle.request.user.has_perm("tardis_portal.add_experimentacl")
        if isinstance(bundle.obj, DatasetACL):
            return bundle.request.user.has_perm("tardis_portal.add_datasetacl")
        if isinstance(bundle.obj, DatafileACL):
            return bundle.request.user.has_perm("tardis_portal.add_datafileacl")
        if isinstance(bundle.obj, Group):
            return bundle.request.user.has_perm("tardis_portal.add_group")
        if isinstance(bundle.obj, Facility):
            return bundle.request.user.has_perm("tardis_portal.add_facility")
        if isinstance(bundle.obj, Instrument):
            facilities = facilities_managed_by(bundle.request.user)
            return all(
                [
                    bundle.request.user.has_perm("tardis_portal.add_instrument"),
                    bundle.obj.facility in facilities,
                ]
            )
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
        """
        Latest TastyPie requires update_detail permissions to be able to create
        objects.  Rather than duplicating code here, we'll just use the same
        authorization rules we use for create_detail.
        """
        return self.create_detail(object_list, bundle)

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")

    def delete_detail(self, object_list, bundle):
        if isinstance(bundle.obj, Experiment):
            return bundle.request.user.has_perm(
                "tardis_portal.change_experiment"
            ) and has_delete_permissions(bundle.request, bundle.obj.id)
        raise Unauthorized("Sorry, no deletes.")


class IntrospectionObject(object):
    def __init__(
        self,
        projects_enabled=None,
        experiment_only_acls=None,
        identifiers_enabled=None,
        identified_objects=[],
        profiles_enabled=None,
        profiled_objects=[],
        id=None,
    ):
        self.projects_enabled = projects_enabled
        self.experiment_only_acls = experiment_only_acls
        self.identifiers_enabled = identifiers_enabled
        self.identified_objects = identified_objects
        self.profiles_enabled = profiles_enabled
        self.profiled_objects = profiled_objects
        self.id = id


class IntrospectionResource(Resource):
    """Tastypie resource for introspection - to expose some key settings publicly"""

    projects_enabled = fields.ApiField(attribute="projects_enabled", null=True)
    experiment_only_acls = fields.ApiField(attribute="experiment_only_acls", null=True)
    identifiers_enabled = fields.ApiField(attribute="identifiers_enabled", null=True)
    identified_objects = fields.ApiField(attribute="identified_objects", null=True)
    profiles_enabled = fields.ApiField(attribute="profiles_enabled", null=True)
    profiled_objects = fields.ApiField(attribute="profiled_objects", null=True)

    class Meta:
        resource_name = "introspection"
        list_allowed_methods = ["get"]
        serializer = default_serializer
        authentication = default_authentication
        object_class = IntrospectionObject
        always_return_data = True

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs["pk"] = bundle_or_obj.obj.id
        else:
            kwargs["pk"] = bundle_or_obj["id"]

        return kwargs

    def get_object_list(self, request):
        try:
            identified_objects = settings.OBJECTS_WITH_IDENTIFIERS
        except Exception:  # Ugly hack should tidy this up to catch specific errors
            identified_objects = []
        try:
            profiled_objects = settings.OBJECTS_WITH_PROFILES
        except Exception:  # Ugly hack should tidy this up to catch specific errors

            profiled_objects = []
        return [
            IntrospectionObject(
                projects_enabled="tardis.apps.projects" in settings.INSTALLED_APPS,
                experiment_only_acls=settings.ONLY_EXPERIMENT_ACLS,
                identifiers_enabled="tardis.apps.identifiers"
                in settings.INSTALLED_APPS,
                identified_objects=identified_objects,
                profiles_enabled="tardis.apps.profiles" in settings.INSTALLED_APPS,
                profiled_objects=profiled_objects,
            )
        ]

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


class GroupResource(ModelResource):
    class Meta:
        object_class = Group
        queryset = Group.objects.all()
        authentication = default_authentication
        authorization = ACLAuthorization()
        filtering = {
            "id": ("exact",),
            "name": ("exact",),
        }


class UserResource(ModelResource):
    groups = fields.ManyToManyField(GroupResource, "groups", null=True, full=True)

    class Meta:
        object_class = User
        authentication = default_authentication
        authorization = ACLAuthorization()
        queryset = User.objects.all().exclude(pk=settings.PUBLIC_USER_ID)
        allowed_methods = ["get"]
        fields = ["username", "first_name", "last_name", "email"]
        serializer = default_serializer
        filtering = {
            "username": ("exact",),
            "email": ("iexact",),
        }

    def dehydrate(self, bundle):
        """
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
        """
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated
        queried_user = bundle.obj
        public_user = (
            queried_user.experiment_set.filter(public_access__gt=1).count() > 0
        )
        same_user = authuser == queried_user

        # add the database id for convenience
        bundle.data["id"] = queried_user.id

        # allow the user to find out their username and email
        # allow facility managers to query other users' username and email
        if authenticated and (same_user or facilities_managed_by(authuser).count() > 0):
            bundle.data["username"] = queried_user.username
            bundle.data["email"] = queried_user.email
        else:
            del bundle.data["username"]
            del bundle.data["email"]

        # add public information
        if public_user:
            bundle.data["email"] = queried_user.email

        return bundle


class MyTardisModelResource(ModelResource):
    class Meta:
        authentication = default_authentication
        authorization = ACLAuthorization()
        serializer = default_serializer
        object_class = None


class FacilityResource(MyTardisModelResource):
    manager_group = fields.ForeignKey(
        GroupResource, "manager_group", null=True, full=True
    )

    # Custom filter for identifiers module based on code example from
    # https://stackoverflow.com/questions/10021749/ \
    # django-tastypie-advanced-filtering-how-to-do-complex-lookups-with-q-objects

    def build_filters(self, filters=None, ignore_bad_filters=False):
        if filters is None:
            filters = {}
        orm_filters = super().build_filters(filters)

        if "tardis.apps.identifiers" in settings.INSTALLED_APPS:
            if "institution" in settings.OBJECTS_WITH_IDENTIFIERS and "pids" in filters:
                query = filters["pids"]
                qset = Q(persistent_id__persistent_id__exact=query) | Q(
                    persistent_id__alternate_ids__contains=query
                )
                orm_filters.update({"pids": qset})
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        if "tardis.apps.identifiers" in settings.INSTALLED_APPS:
            if (
                "institution" in settings.OBJECTS_WITH_IDENTIFIERS
                and "pids" in applicable_filters
            ):
                custom = applicable_filters.pop("pids")
            else:
                custom = None
        else:
            custom = None

        semi_filtered = super().apply_filters(request, applicable_filters)

        return semi_filtered.filter(custom) if custom else semi_filtered

    # End of custom filter code

    class Meta(MyTardisModelResource.Meta):
        object_class = Facility
        queryset = Facility.objects.all()
        filtering = {
            "id": ("exact",),
            "manager_group": ALL_WITH_RELATIONS,
            "name": ("exact",),
        }
        ordering = ["id", "name"]
        always_return_data = True

    def dehydrate(self, bundle):
        facility = bundle.obj
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "facility" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            bundle.data["persistent_id"] = facility.persistent_id.persistent_id
            bundle.data["alternate_ids"] = facility.persistent_id.alternate_ids
        return bundle


class InstrumentResource(MyTardisModelResource):
    facility = fields.ForeignKey(FacilityResource, "facility", null=True, full=True)

    # Custom filter for identifiers module based on code example from
    # https://stackoverflow.com/questions/10021749/ \
    # django-tastypie-advanced-filtering-how-to-do-complex-lookups-with-q-objects

    def build_filters(self, filters=None, ignore_bad_filters=False):
        if filters is None:
            filters = {}
        orm_filters = super().build_filters(filters)

        if "tardis.apps.identifiers" in settings.INSTALLED_APPS:
            if "institution" in settings.OBJECTS_WITH_IDENTIFIERS and "pids" in filters:
                query = filters["pids"]
                qset = Q(persistent_id__persistent_id__exact=query) | Q(
                    persistent_id__alternate_ids__contains=query
                )
                orm_filters.update({"pids": qset})
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        if "tardis.apps.identifiers" in settings.INSTALLED_APPS:
            if (
                "institution" in settings.OBJECTS_WITH_IDENTIFIERS
                and "pids" in applicable_filters
            ):
                custom = applicable_filters.pop("pids")
            else:
                custom = None
        else:
            custom = None

        semi_filtered = super().apply_filters(request, applicable_filters)

        return semi_filtered.filter(custom) if custom else semi_filtered

    # End of custom filter code

    class Meta(MyTardisModelResource.Meta):
        object_class = Instrument
        queryset = Instrument.objects.all()
        filtering = {
            "id": ("exact",),
            "facility": ALL_WITH_RELATIONS,
            "name": ("exact",),
        }
        ordering = ["id", "name"]
        always_return_data = True

    def dehydrate(self, bundle):
        instrument = bundle.obj
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "instrument" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            bundle.data["persistent_id"] = instrument.persistent_id.persistent_id
            bundle.data["alternate_ids"] = instrument.persistent_id.alternate_ids
        return bundle


class ExperimentResource(MyTardisModelResource):
    """API for Experiments
    also creates a default ACL and allows ExperimentParameterSets to be read
    and written.

    TODO: catch duplicate schema submissions for parameter sets
    """

    created_by = fields.ForeignKey(UserResource, "created_by")
    parameter_sets = fields.ToManyField(
        "tardis.tardis_portal.api.ExperimentParameterSetResource",
        "experimentparameterset_set",
        related_name="experiment",
        full=True,
        null=True,
    )
    tags = fields.ListField()

    # Custom filter for identifiers module based on code example from
    # https://stackoverflow.com/questions/10021749/ \
    # django-tastypie-advanced-filtering-how-to-do-complex-lookups-with-q-objects

    def build_filters(self, filters=None, ignore_bad_filters=False):
        if filters is None:
            filters = {}
        orm_filters = super().build_filters(filters)

        if "tardis.apps.identifiers" in settings.INSTALLED_APPS:
            if "institution" in settings.OBJECTS_WITH_IDENTIFIERS and "pids" in filters:
                query = filters["pids"]
                qset = Q(persistent_id__persistent_id__exact=query) | Q(
                    persistent_id__alternate_ids__contains=query
                )
                orm_filters.update({"pids": qset})
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        if "tardis.apps.identifiers" in settings.INSTALLED_APPS:
            if (
                "institution" in settings.OBJECTS_WITH_IDENTIFIERS
                and "pids" in applicable_filters
            ):
                custom = applicable_filters.pop("pids")
            else:
                custom = None
        else:
            custom = None

        semi_filtered = super().apply_filters(request, applicable_filters)

        return semi_filtered.filter(custom) if custom else semi_filtered

    # End of custom filter code

    def dehydrate_tags(self, bundle):
        return list(map(str, bundle.obj.tags.all()))

    def save_m2m(self, bundle):
        tags = bundle.data.get("tags", [])
        bundle.obj.tags.set(*tags)
        return super().save_m2m(bundle)

    class Meta(MyTardisModelResource.Meta):
        object_class = Experiment
        queryset = Experiment.objects.all()
        filtering = {
            "id": ("exact",),
            "title": ("exact",),
        }
        ordering = ["id", "title", "created_time", "update_time"]
        always_return_data = True

    def dehydrate(self, bundle):
        exp = bundle.obj
        authors = [
            {"name": a.author, "url": a.url} for a in exp.experimentauthor_set.all()
        ]
        bundle.data["authors"] = authors
        lic = exp.license
        if lic is not None:
            bundle.data["license"] = {
                "name": lic.name,
                "url": lic.url,
                "description": lic.internal_description,
                "image_url": lic.image_url,
                "allows_distribution": lic.allows_distribution,
            }
        owners = exp.get_owners()
        bundle.data["owner_ids"] = [o.id for o in owners]

        if settings.ONLY_EXPERIMENT_ACLS:
            dataset_count = exp.datasets.all().count()
        else:
            dataset_count = (
                Dataset.safe.all(bundle.request.user)
                .filter(experiments__id=exp.id)
                .count()
            )
        bundle.data["dataset_count"] = dataset_count
        datafile_count = exp.get_datafiles(bundle.request.user).count()
        bundle.data["datafile_count"] = datafile_count
        experiment_size = exp.get_size(bundle.request.user)
        bundle.data["experiment_size"] = experiment_size

        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            bundle.data["persistent_id"] = exp.persistent_id.persistent_id
            bundle.data["alternate_ids"] = exp.persistent_id.alternate_ids

        return bundle

    def hydrate_m2m(self, bundle):
        """
        create ACL before any related objects are created in order to use
        ACL permissions for those objects.
        """
        if getattr(bundle.obj, "id", False):
            experiment = bundle.obj
            # TODO: unify this with the view function's ACL creation,
            # maybe through an ACL toolbox.
            acl = ExperimentACL(
                experiment=experiment,
                user=bundle.request.user,
                canRead=True,
                canDownload=True,
                canWrite=True,
                canDelete=True,
                canSensitive=True,
                isOwner=True,
                aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
            acl.save()

        return super().hydrate_m2m(bundle)

    def obj_create(self, bundle, **kwargs):
        """experiments need at least one ACL to be available through the
        ExperimentManager (Experiment.safe)
        Currently not tested for failed db transactions as sqlite does not
        enforce limits.
        """
        user = bundle.request.user
        bundle.data["created_by"] = user
        with transaction.atomic():
            # Clean up bundle to remove PIDS if the identifiers app is being used.
            if (
                "tardis.apps.identifiers" in settings.INSTALLED_APPS
                and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
            ):
                pid = None
                alternate_ids = None
                if "persistent_id" in bundle.data.keys():
                    pid = bundle.data.pop("persistent_id")
                if "alternate_ids" in bundle.data.keys():
                    alternate_ids = bundle.data.pop("alternate_ids")
            bundle = super().obj_create(bundle, **kwargs)
            # After the obj has been created
            if (
                "tardis.apps.identifiers" in settings.INSTALLED_APPS
                and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
            ):
                experiment = bundle.obj
                pid_obj = experiment.persistent_id
                if pid:
                    pid_obj.persistent_id = pid
                if alternate_ids:
                    pid_obj.alternate_ids = alternate_ids
                pid_obj.save()
            if bundle.data.get("users", False):
                for entry in bundle.data["users"]:
                    username, isOwner, canDownload, canSensitive = entry
                    acl_user = get_or_create_user(username)
                    ExperimentACL.objects.create(
                        experiment=experiment,
                        user=acl_user,
                        canRead=True,
                        canDownload=canDownload,
                        canSensitive=canSensitive,
                        isOwner=isOwner,
                    )
            if bundle.data.get("groups", False):
                for entry in bundle.data["groups"]:
                    groupname, isOwner, canDownload, canSensitive = entry
                    acl_group, _ = Group.objects.get_or_create(name=groupname)
                    ExperimentACL.objects.create(
                        experiment=experiment,
                        group=acl_group,
                        canRead=True,
                        canDownload=canDownload,
                        canSensitive=canSensitive,
                        isOwner=isOwner,
                    )
            if not any(
                [bundle.data.get("users", False), bundle.data.get("groups", False)]
            ):
                for parent in experiment.projects.all():
                    for parent_acl in parent.projectacl_set.all():
                        ExperimentACL.objects.create(
                            experiment=experiment,
                            user=parent_acl.user,
                            group=parent_acl.group,
                            token=parent_acl.token,
                            canRead=parent_acl.canRead,
                            canDownload=parent_acl.canDownload,
                            canWrite=parent_acl.canWrite,
                            canSensitive=parent_acl.canSensitive,
                            canDelete=parent_acl.canDelete,
                            isOwner=parent_acl.isOwner,
                            effectiveDate=parent_acl.effectiveDate,
                            expiryDate=parent_acl.expiryDate,
                            aclOwnershipType=parent_acl.aclOwnershipType,
                        )
            return bundle


class ExperimentAuthorResource(MyTardisModelResource):
    """API for ExperimentAuthors"""

    experiment = fields.ForeignKey(
        ExperimentResource, "experiment", full=True, null=True
    )

    class Meta(MyTardisModelResource.Meta):
        object_class = ExperimentAuthor
        queryset = ExperimentAuthor.objects.all()
        filtering = {
            "id": ("exact",),
            "experiment": ALL_WITH_RELATIONS,
            "author": ("exact", "iexact"),
            "institution": ("exact", "iexact"),
            "email": ("exact", "iexact"),
            "order": ("exact",),
            "url": ("exact", "iexact"),
        }
        ordering = ["id", "author", "email", "order"]
        always_return_data = True


class DatasetResource(MyTardisModelResource):
    experiments = fields.ToManyField(
        ExperimentResource, "experiments", related_name="datasets"
    )
    parameter_sets = fields.ToManyField(
        "tardis.tardis_portal.api.DatasetParameterSetResource",
        "datasetparameterset_set",
        related_name="dataset",
        full=True,
        null=True,
    )
    instrument = fields.ForeignKey(
        InstrumentResource, "instrument", null=True, full=True
    )
    tags = fields.ListField()

    # Custom filter for identifiers module based on code example from
    # https://stackoverflow.com/questions/10021749/ \
    # django-tastypie-advanced-filtering-how-to-do-complex-lookups-with-q-objects

    def build_filters(self, filters=None, ignore_bad_filters=False):
        if filters is None:
            filters = {}
        orm_filters = super().build_filters(filters)

        if "tardis.apps.identifiers" in settings.INSTALLED_APPS:
            if "institution" in settings.OBJECTS_WITH_IDENTIFIERS and "pids" in filters:
                query = filters["pids"]
                qset = Q(persistent_id__persistent_id__exact=query) | Q(
                    persistent_id__alternate_ids__contains=query
                )
                orm_filters.update({"pids": qset})
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        if "tardis.apps.identifiers" in settings.INSTALLED_APPS:
            if (
                "institution" in settings.OBJECTS_WITH_IDENTIFIERS
                and "pids" in applicable_filters
            ):
                custom = applicable_filters.pop("pids")
            else:
                custom = None
        else:
            custom = None

        semi_filtered = super().apply_filters(request, applicable_filters)

        return semi_filtered.filter(custom) if custom else semi_filtered

    # End of custom filter code

    class Meta(MyTardisModelResource.Meta):
        object_class = Dataset
        queryset = Dataset.objects.all()
        filtering = {
            "id": ("exact",),
            "experiments": ALL_WITH_RELATIONS,
            "description": ("exact",),
            "directory": ("exact",),
            "instrument": ALL_WITH_RELATIONS,
        }
        ordering = ["id", "description"]
        always_return_data = True

    def dehydrate_tags(self, bundle):
        return list(map(str, bundle.obj.tags.all()))

    def save_m2m(self, bundle):
        tags = bundle.data.get("tags", [])
        bundle.obj.tags.set(*tags)
        return super().save_m2m(bundle)

    def dehydrate(self, bundle):
        dataset = bundle.obj
        size = dataset.get_size(bundle.request.user)
        bundle.data["dataset_size"] = size
        dataset_experiment_count = dataset.experiments.count()
        bundle.data["dataset_experiment_count"] = dataset_experiment_count
        if settings.ONLY_EXPERIMENT_ACLS:
            dataset_datafile_count = dataset.datafile_set.count()
        else:
            dataset_datafile_count = (
                DataFile.safe.all(bundle.request.user)
                .filter(dataset__id=dataset.id)
                .count()
            )
        bundle.data["dataset_datafile_count"] = dataset_datafile_count
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "dataset" in settings.OBJECTS_WITH_IDENTIFIERS
        ):
            bundle.data["persistent_id"] = dataset.persistent_id.persistent_id
            bundle.data["alternate_ids"] = dataset.persistent_id.alternate_ids
        return bundle

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/files/"
                r"(?:(?P<file_path>.+))?$" % self._meta.resource_name,
                self.wrap_view("get_datafiles"),
                name="api_get_datafiles_for_dataset",
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/root-dir-nodes%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("get_root_dir_nodes"),
                name="api_get_root_dir_nodes",
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/child-dir-nodes%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("get_child_dir_nodes"),
                name="api_get_child_dir_nodes",
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/child-dir-files%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("get_child_dir_files"),
                name="api_get_child_dir_files",
            ),
        ]

    def get_datafiles(self, request, **kwargs):
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)

        dataset_id = kwargs["pk"]
        del kwargs["pk"]

        file_path = kwargs.get("file_path", None)

        if not has_access(request, dataset_id, "dataset"):
            return HttpResponseForbidden()

        kwargs["dataset__id"] = dataset_id

        if file_path is not None:
            del kwargs["file_path"]
            kwargs["directory__startswith"] = file_path

        return DataFileResource().dispatch("list", request, **kwargs)

    def hydrate_m2m(self, bundle):
        """
        Create experiment-dataset associations first, because they affect
        authorization for adding other related resources, e.g. metadata
        """
        if getattr(bundle.obj, "id", False):
            for exp_uri in bundle.data.get("experiments", []):
                try:
                    exp = ExperimentResource.get_via_uri(
                        ExperimentResource(), exp_uri, bundle.request
                    )
                    bundle.obj.experiments.add(exp)
                except NotFound:
                    pass
        return super().hydrate_m2m(bundle)

    def get_root_dir_nodes(self, request, **kwargs):
        """Return JSON-serialized list of filenames/folders in the dataset's root directory"""
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)

        dataset_id = kwargs["pk"]
        dataset = Dataset.objects.get(id=dataset_id)
        if not has_access(request, dataset_id, "dataset"):
            return HttpResponseForbidden()

        # get dirs at root level
        dir_tuples = dataset.get_dir_tuples(request.user, "")
        # get files at root level
        if settings.ONLY_EXPERIMENT_ACLS:
            dfs = (
                DataFile.objects.filter(dataset=dataset, directory="")
                | DataFile.objects.filter(dataset=dataset, directory__isnull=True)
            ).distinct()
        else:
            dfs = (
                DataFile.safe.all(request.user).filter(dataset=dataset, directory="")
                | DataFile.safe.all(request.user).filter(
                    dataset=dataset, directory__isnull=True
                )
            ).distinct()

        pgresults = 1000

        paginator = Paginator(dfs, pgresults)

        try:
            page_num = int(request.GET.get("page", "0"))
        except ValueError:
            page_num = 0

        # If page request (9999) is out of range, deliver last page of results.

        try:
            dfs = paginator.page(page_num + 1)
        except (EmptyPage, InvalidPage):
            dfs = paginator.page(paginator.num_pages)
        child_list = []
        # append directories list
        if dir_tuples and page_num == 0:
            for dir_tuple in dir_tuples:
                child_dict = {
                    "name": dir_tuple[0],
                    "path": dir_tuple[1],
                    "children": [],
                }
                child_list.append(child_dict)
                # append files to list
        if dfs:
            for df in dfs:
                children = {}
                children["name"] = df.filename
                children["verified"] = df.verified
                children["id"] = df.id
                children["is_online"] = df.is_online
                children["recall_url"] = df.recall_url
                child_list.append(children)
        if paginator.num_pages - 1 > page_num:
            # append a marker element
            children = {}
            children["next_page"] = True
            children["next_page_num"] = page_num + 1
            children["display_text"] = "Displaying {current} of {total} ".format(
                current=(dfs.number * pgresults), total=paginator.count
            )
            child_list.append(children)
        if paginator.num_pages - 1 == page_num:
            # append a marker element
            children = {}
            children["next_page"] = False
            child_list.append(children)

        return JsonResponse(child_list, status=200, safe=False)

    def get_child_dir_nodes(self, request, **kwargs):
        """Return JSON-serialized list of filenames/folders within a child subdirectory"""
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)

        dataset_id = kwargs["pk"]
        if not has_access(request, dataset_id, "dataset"):
            return HttpResponseForbidden()

        base_dir = request.GET.get("dir_path", None)
        dataset = Dataset.objects.get(id=dataset_id)
        if not base_dir:
            return HttpResponse("Please specify base directory", status=400)

        # Previously this method checked the tree nodes data passed
        # in to determine whether children has already been loaded,
        # but now that logic will be moved to the front-end component.

        # list dir under base_dir
        child_dir_tuples = dataset.get_dir_tuples(request.user, base_dir)
        # list files under base_dir
        if settings.ONLY_EXPERIMENT_ACLS:
            dfs = DataFile.objects.filter(dataset=dataset, directory=base_dir)
        else:
            dfs = DataFile.safe.all(request.user).filter(
                dataset=dataset, directory=base_dir
            )
        # walk the directory tree and append files and dirs
        # if there are directories append this to data
        child_list = []
        if child_dir_tuples:
            child_list = dataset.get_dir_nodes(child_dir_tuples)

        # if there are files append this
        if dfs:
            for df in dfs:
                child = {
                    "name": df.filename,
                    "id": df.id,
                    "verified": df.verified,
                    "is_online": df.is_online,
                    "recall_url": df.recall_url,
                }
                child_list.append(child)

        return JsonResponse(child_list, status=200, safe=False)

    def get_child_dir_files(self, request, **kwargs):
        """
        Return a list of datafile Ids within a child subdirectory
        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        :param kwargs:
        :return: a list of datafile IDs
        :rtype: JsonResponse: :class: `django.http.JsonResponse`
        """
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)
        dataset_id = kwargs["pk"]
        if not has_access(request, dataset_id, "dataset"):
            return HttpResponseForbidden()

        dir_path = request.GET.get("dir_path", None)
        if not dir_path:
            return HttpResponse("Please specify folder path")

        if settings.ONLY_EXPERIMENT_ACLS:
            df_list = DataFile.objects.filter(
                dataset__id=dataset_id, directory=dir_path
            ) | DataFile.objects.filter(
                dataset__id=dataset_id, directory__startswith=dir_path + "/"
            )
        else:
            df_list = DataFile.safe.all(request.user).filter(
                dataset__id=dataset_id, directory=dir_path
            ) | DataFile.safe.all(request.user).filter(
                dataset__id=dataset_id, directory__startswith=dir_path + "/"
            )
        ids = [df.id for df in df_list]
        return JsonResponse(ids, status=200, safe=False)

    def _populate_children(self, request, sub_child_dirs, dir_node, dataset):
        """Populate the children list in a directory node

        Example dir_node: {'name': u'child_1', 'children': []}
        """
        for dir in sub_child_dirs:
            part1, part2 = dir
            # get files for this dir
            if settings.ONLY_EXPERIMENT_ACLS:
                dfs = DataFile.objects.filter(dataset=dataset, directory=part2)
            else:
                dfs = DataFile.safe.all(request.user).filter(
                    dataset=dataset, directory=part2
                )
            filenames = [df.filename for df in dfs]
            if part1 == "..":
                for file_name in filenames:
                    child = {"name": file_name}
                    dir_node["children"].append(child)
            else:
                children = []
                for file_name in filenames:
                    child = {"name": file_name}
                    children.append(child)
                dir_node["children"].append(
                    {"name": part2.rpartition("/")[2], "children": children}
                )

    def obj_create(self, bundle, **kwargs):
        with transaction.atomic():
            # Clean up bundle to remove PIDS if the identifiers app is being used.
            if (
                "tardis.apps.identifiers" in settings.INSTALLED_APPS
                and "dataset" in settings.OBJECTS_WITH_IDENTIFIERS
            ):
                pid = None
                alternate_ids = None
                if "persistent_id" in bundle.data.keys():
                    pid = bundle.data.pop("persistent_id")
                if "alternate_ids" in bundle.data.keys():
                    alternate_ids = bundle.data.pop("alternate_ids")
            bundle = super().obj_create(bundle, **kwargs)
            # After the obj has been created
            if (
                "tardis.apps.identifiers" in settings.INSTALLED_APPS
                and "dataset" in settings.OBJECTS_WITH_IDENTIFIERS
            ):
                dataset = bundle.obj
                pid_obj = dataset.persistent_id
                if pid:
                    pid_obj.persistent_id = pid
                if alternate_ids:
                    pid_obj.alternate_ids = alternate_ids
                pid_obj.save()
            if bundle.data.get("users", False):
                for entry in bundle.data["users"]:
                    username, isOwner, canDownload, canSensitive = entry
                    acl_user = get_or_create_user(username)
                    DatasetACL.objects.create(
                        dataset=dataset,
                        user=acl_user,
                        canRead=True,
                        canDownload=canDownload,
                        canSensitive=canSensitive,
                        isOwner=isOwner,
                    )
            if bundle.data.get("groups", False):
                for entry in bundle.data["groups"]:
                    groupname, isOwner, canDownload, canSensitive = entry
                    acl_group, _ = Group.objects.get_or_create(name=groupname)
                    DatasetACL.objects.create(
                        dataset=dataset,
                        group=acl_group,
                        canRead=True,
                        canDownload=canDownload,
                        canSensitive=canSensitive,
                        isOwner=isOwner,
                    )
            if not any(
                [bundle.data.get("users", False), bundle.data.get("groups", False)]
            ):
                for parent in dataset.experiments.all():
                    for parent_acl in parent.experimentacl_set.all():
                        DatasetACL.objects.create(
                            dataset=dataset,
                            user=parent_acl.user,
                            group=parent_acl.group,
                            token=parent_acl.token,
                            canRead=parent_acl.canRead,
                            canDownload=parent_acl.canDownload,
                            canWrite=parent_acl.canWrite,
                            canSensitive=parent_acl.canSensitive,
                            canDelete=parent_acl.canDelete,
                            isOwner=parent_acl.isOwner,
                            effectiveDate=parent_acl.effectiveDate,
                            expiryDate=parent_acl.expiryDate,
                            aclOwnershipType=parent_acl.aclOwnershipType,
                        )
            return bundle


class DataFileResource(MyTardisModelResource):
    dataset = fields.ForeignKey(DatasetResource, "dataset")
    parameter_sets = fields.ToManyField(
        "tardis.tardis_portal.api.DatafileParameterSetResource",
        "datafileparameterset_set",
        related_name="datafile",
        full=True,
        null=True,
    )
    datafile = fields.FileField()
    replicas = fields.ToManyField(
        "tardis.tardis_portal.api.ReplicaResource",
        "file_objects",
        related_name="datafile",
        full=True,
        null=True,
    )
    temp_url = None
    tags = fields.ListField()

    def dehydrate_tags(self, bundle):
        return list(map(str, bundle.obj.tags.all()))

    def save_m2m(self, bundle):
        tags = bundle.data.get("tags", [])
        bundle.obj.tags.set(*tags)
        return super().save_m2m(bundle)

    class Meta(MyTardisModelResource.Meta):
        object_class = DataFile
        queryset = DataFile.objects.all()
        filtering = {
            "directory": ("exact", "startswith"),
            "dataset": ALL_WITH_RELATIONS,
            "filename": ("exact",),
        }
        ordering = ["id", "filename", "modification_time"]
        resource_name = "dataset_file"

    def download_file(self, request, **kwargs):
        """
        curl needs the -J switch to get the filename right
        auth needs to be added manually here
        """
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)
        self.throttle_check(request)

        if not has_download_access(request, kwargs["pk"], "datafile"):
            return HttpResponseForbidden()

        file_record = self._meta.queryset.get(pk=kwargs["pk"])
        self.authorized_read_detail(
            [file_record], self.build_bundle(obj=file_record, request=request)
        )

        preferred_dfo = file_record.get_preferred_dfo()
        if not preferred_dfo:
            # No verified DataFileObject exists for this DataFile
            return HttpResponseNotFound()

        storage_class_name = preferred_dfo.storage_box.django_storage_class
        download_uri_templates = getattr(settings, "DOWNLOAD_URI_TEMPLATES", {})
        if storage_class_name in download_uri_templates:
            template = URITemplate(download_uri_templates[storage_class_name])
            return redirect(template.expand(dfo_id=preferred_dfo.id))

        if settings.PROXY_DOWNLOADS:
            full_path = preferred_dfo.get_full_path()
            for dir_prefix, url_prefix in settings.PROXY_DOWNLOAD_PREFIXES:
                if full_path.startswith(dir_prefix):
                    response = HttpResponse()
                    response["Content-Disposition"] = "attachment; filename={0}".format(
                        file_record.filename
                    )
                    path = full_path.split(dir_prefix)[1]
                    response["X-Accel-Redirect"] = "%s/%s" % (url_prefix, path)
                    return response

        # Log file download event
        if getattr(settings, "ENABLE_EVENTLOG", False):
            from tardis.apps.eventlog.utils import log

            log(
                action="DOWNLOAD_DATAFILE",
                extra={"id": kwargs["pk"], "type": "api"},
                request=request,
            )

        file_object = file_record.get_file()
        wrapper = FileWrapper(file_object)
        tracker_data = dict(
            label="file",
            session_id=request.COOKIES.get("_ga"),
            ip=request.META.get("REMOTE_ADDR", ""),
            user=request.user,
            total_size=file_record.size,
            num_files=1,
            ua=request.META.get("HTTP_USER_AGENT", None),
        )
        response = StreamingHttpResponse(
            IteratorTracker(wrapper, tracker_data), content_type=file_record.mimetype
        )
        response["Content-Length"] = file_record.size
        response["Content-Disposition"] = (
            'attachment; filename="%s"' % file_record.filename
        )
        self.log_throttled_access(request)
        return response

    def verify_file(self, request, **kwargs):
        """triggers verification of file, e.g. after non-POST upload complete"""
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)
        self.throttle_check(request)

        if not has_download_access(request, kwargs["pk"], "datafile"):
            return HttpResponseForbidden()

        file_record = self._meta.queryset.get(pk=kwargs["pk"])
        self.authorized_read_detail(
            [file_record], self.build_bundle(obj=file_record, request=request)
        )
        for dfo in file_record.file_objects.all():
            shadow = "dfo_verify location:%s" % dfo.storage_box.name
            tasks.dfo_verify.apply_async(
                args=[dfo.id], priority=dfo.priority, shadow=shadow
            )
        return HttpResponse()

    def hydrate(self, bundle):
        if "attached_file" in bundle.data:
            # have POSTed file
            newfile = bundle.data["attached_file"][0]
            compute_md5 = getattr(settings, "COMPUTE_MD5", True)
            compute_sha512 = getattr(settings, "COMPUTE_SHA512", False)
            if (compute_md5 and "md5sum" not in bundle.data) or (
                compute_sha512 and "sha512sum" not in bundle.data
            ):
                checksums = compute_checksums(
                    newfile,
                    compute_md5=compute_md5,
                    compute_sha512=compute_sha512,
                    close_file=False,
                )
                if compute_md5:
                    bundle.data["md5sum"] = checksums["md5sum"]
                if compute_sha512:
                    bundle.data["sha512sum"] = checksums["sha512sum"]

            if "replicas" in bundle.data:
                for replica in bundle.data["replicas"]:
                    replica.update({"file_object": newfile})
            else:
                bundle.data["replicas"] = [{"file_object": newfile}]

            del bundle.data["attached_file"]

        return bundle

    def obj_create(self, bundle, **kwargs):
        """
        Creates a new DataFile object from the provided bundle.data dict.

        If a duplicate key error occurs, responds with HTTP Error 409: CONFLICT
        """
        with transaction.atomic():
            if (
                "tardis.apps.identifiers" in settings.INSTALLED_APPS
                and "datafile" in settings.OBJECTS_WITH_IDENTIFIERS
            ):
                pid = None
                alternate_ids = None
                if "persistent_id" in bundle.data.keys():
                    pid = bundle.data.pop("persistent_id")
                if "alternate_ids" in bundle.data.keys():
                    alternate_ids = bundle.data.pop("alternate_ids")
            try:
                retval = super().obj_create(bundle, **kwargs)
            except IntegrityError as err:
                if "duplicate key" in str(err):
                    raise ImmediateHttpResponse(HttpResponse(status=409))
                raise

            if "replicas" not in bundle.data or not bundle.data["replicas"]:
                # no replica specified: return upload path and create dfo for
                # new path
                sbox = bundle.obj.get_receiving_storage_box()
                if sbox is None:
                    raise NotImplementedError
                dfo = DataFileObject(datafile=bundle.obj, storage_box=sbox)
                dfo.create_set_uri()
                dfo.save()
                self.temp_url = dfo.get_full_path()
            else:
                # Log file upload event
                if getattr(settings, "ENABLE_EVENTLOG", False):
                    from tardis.apps.eventlog.utils import log

                    log(
                        action="UPLOAD_DATAFILE",
                        extra={"id": bundle.obj.id, "type": "post"},
                        request=bundle.request,
                    )

            # After the obj has been created
            if (
                "tardis.apps.identifiers" in settings.INSTALLED_APPS
                and "datafile" in settings.OBJECTS_WITH_IDENTIFIERS
            ):
                datafile = retval.obj
                pid_obj = datafile.persistent_id
                if pid:
                    pid_obj.persistent_id = pid
                if alternate_ids:
                    pid_obj.alternate_ids = alternate_ids
                pid_obj.save()
            if bundle.data.get("users", False):
                for entry in bundle.data["users"]:
                    username, isOwner, canDownload, canSensitive = entry
                    acl_user = get_or_create_user(username)
                    DatafileACL.objects.create(
                        datafile=datafile,
                        user=acl_user,
                        canRead=True,
                        canDownload=canDownload,
                        canSensitive=canSensitive,
                        isOwner=isOwner,
                    )
            if bundle.data.get("groups", False):
                for entry in bundle.data["groups"]:
                    groupname, isOwner, canDownload, canSensitive = entry
                    acl_group, _ = Group.objects.get_or_create(name=groupname)
                    DatafileACL.objects.create(
                        datafile=datafile,
                        group=acl_group,
                        canRead=True,
                        canDownload=canDownload,
                        canSensitive=canSensitive,
                        isOwner=isOwner,
                    )
            if not any(
                [bundle.data.get("users", False), bundle.data.get("groups", False)]
            ):
                print("before")
                print(datafile)
                parent = Dataset.objects.get(pk=datafile.dataset.id)
                print("after")
                """for parent_acl in parent.datasetacl_set.all():
                    DatafileACL.objects.create(
                        datafile=datafile,
                        user=parent_acl.user,
                        group=parent_acl.group,
                        token=parent_acl.token,
                        canRead=parent_acl.canRead,
                        canDownload=parent_acl.canDownload,
                        canWrite=parent_acl.canWrite,
                        canSensitive=parent_acl.canSensitive,
                        canDelete=parent_acl.canDelete,
                        isOwner=parent_acl.isOwner,
                        effectiveDate=parent_acl.effectiveDate,
                        expiryDate=parent_acl.expiryDate,
                        aclOwnershipType=parent_acl.aclOwnershipType,
                    )"""
        return retval

    def post_list(self, request, **kwargs):
        response = super().post_list(request, **kwargs)
        if self.temp_url is not None:
            response.content = self.temp_url
            self.temp_url = None
        return response

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/download%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("download_file"),
                name="api_download_file",
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/verify%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("verify_file"),
                name="api_verify_file",
            ),
        ]

    def deserialize(self, request, data, format=None):
        """
        from https://github.com/toastdriven/django-tastypie/issues/42
        modified to deserialize json sent via POST. Would fail if data is sent
        in a different format.
        uses a hack to get back pure json from request.POST
        """
        if not format:
            format = request.META.get("CONTENT_TYPE", "application/json")
        if format == "application/x-www-form-urlencoded":
            return request.POST
        if format.startswith("multipart"):
            jsondata = request.POST["json_data"]
            data = json.loads(jsondata)
            data.update(request.FILES)
            return data
        return super().deserialize(request, data, format)

    def put_detail(self, request, **kwargs):
        """
        from https://github.com/toastdriven/django-tastypie/issues/42
        """
        if request.META.get("CONTENT_TYPE").startswith("multipart") and not hasattr(
            request, "_body"
        ):
            request._body = ""

        return super().put_detail(request, **kwargs)


class SchemaResource(MyTardisModelResource):
    class Meta(MyTardisModelResource.Meta):
        object_class = Schema
        queryset = Schema.objects.all()
        filtering = {
            "id": ("exact",),
            "namespace": ("exact",),
        }
        ordering = ["id"]


class ParameterNameResource(MyTardisModelResource):
    schema = fields.ForeignKey(SchemaResource, "schema")

    class Meta(MyTardisModelResource.Meta):
        object_class = ParameterName
        queryset = ParameterName.objects.all()
        filtering = {
            "schema": ALL_WITH_RELATIONS,
        }


class ParameterResource(MyTardisModelResource):
    name = fields.ForeignKey(ParameterNameResource, "name")
    value = fields.CharField(blank=True)

    def hydrate(self, bundle):
        """
        sets the parametername by uri or name
        if untyped value is given, set value via parameter method,
        otherwise use modelresource automatisms
        """
        try:
            parname = ParameterNameResource.get_via_uri(
                ParameterNameResource(), bundle.data["name"], bundle.request
            )
        except NotFound:
            parname = bundle.related_obj._get_create_parname(bundle.data["name"])
        del bundle.data["name"]
        bundle.obj.name = parname
        if "value" in bundle.data:
            bundle.obj.set_value(bundle.data["value"])
            del bundle.data["value"]
        return bundle


class ParameterSetResource(MyTardisModelResource):
    schema = fields.ForeignKey(SchemaResource, "schema", full=True)

    def hydrate_schema(self, bundle):
        try:
            schema = SchemaResource.get_via_uri(
                SchemaResource(), bundle.data["schema"], bundle.request
            )
        except NotFound:
            schema = Schema.objects.get(namespace=bundle.data["schema"])
        bundle.obj.schema = schema
        del bundle.data["schema"]
        return bundle


class LocationResource(MyTardisModelResource):
    class Meta(MyTardisModelResource.Meta):
        queryset = StorageBox.objects.all()


class ReplicaResource(MyTardisModelResource):
    datafile = fields.ForeignKey(DataFileResource, "datafile")

    class Meta(MyTardisModelResource.Meta):
        object_class = DataFileObject
        queryset = DataFileObject.objects.all()
        filtering = {
            "verified": ("exact",),
            "url": ("exact", "startswith"),
        }
        ordering = ["id"]

    def hydrate(self, bundle):
        if "url" in bundle.data:
            if "file_object" not in bundle.data:
                bundle.data["uri"] = bundle.data["url"]
            del bundle.data["url"]
        datafile = bundle.related_obj
        bundle.obj.datafile = datafile
        bundle.data["datafile"] = datafile
        if "location" in bundle.data:
            try:
                bundle.obj.storage_box = StorageBox.objects.get(
                    name=bundle.data["location"]
                )
            except StorageBox.DoesNotExist:
                bundle.obj.storage_box = datafile.get_default_storage_box()
            del bundle.data["location"]
        else:
            bundle.obj.storage_box = datafile.get_default_storage_box()

        bundle.obj.save()
        if "file_object" in bundle.data:
            bundle.obj.file_object = bundle.data["file_object"]
            bundle.data["file_object"].close()
            del bundle.data["file_object"]
            bundle.obj = DataFileObject.objects.get(id=bundle.obj.id)
        return bundle

    def dehydrate(self, bundle):
        dfo = bundle.obj
        bundle.data["location"] = dfo.storage_box.name
        return bundle


class ExperimentACLResource(MyTardisModelResource):
    experiment = fields.ForeignKey(ExperimentResource, "experiment")

    class Meta:
        object_class = ExperimentACL
        authentication = default_authentication
        authorization = ACLAuthorization()
        queryset = ExperimentACL.objects.select_related("user").exclude(
            user__id=settings.PUBLIC_USER_ID
        )
        # filtering = {
        #    'pluginId': ('exact', ),
        #    'entityId': ('exact', ),
        # }
        ordering = ["id"]

    def hydrate(self, bundle):
        try:
            experiment = ExperimentResource.get_via_uri(
                ExperimentResource(), bundle.data["experiment"], bundle.request
            )
        except NotFound:
            experiment = Experiment.objects.get(namespace=bundle.data["experiment"])
        bundle.obj.experiment = experiment
        del bundle.data["experiment"]
        return bundle


class DatasetACLResource(MyTardisModelResource):
    dataset = fields.ForeignKey(DatasetResource, "dataset")

    class Meta:
        object_class = DatasetACL
        authentication = default_authentication
        authorization = ACLAuthorization()
        queryset = DatasetACL.objects.select_related("user").exclude(
            user__id=settings.PUBLIC_USER_ID
        )
        filtering = {
            "pluginId": ("exact",),
            "entityId": ("exact",),
        }
        ordering = ["id"]

    def hydrate(self, bundle):
        try:
            dataset = DatasetResource.get_via_uri(
                DatasetResource(), bundle.data["dataset"], bundle.request
            )
        except NotFound:
            dataset = Dataset.objects.get(namespace=bundle.data["dataset"])
        bundle.obj.dataset = dataset
        del bundle.data["dataset"]
        return bundle


class DatafileACLResource(MyTardisModelResource):
    datafile = fields.ForeignKey(DataFileResource, "datafile")

    class Meta:
        object_class = DatafileACL
        authentication = default_authentication
        authorization = ACLAuthorization()
        queryset = DatafileACL.objects.select_related("user").exclude(
            user__id=settings.PUBLIC_USER_ID
        )
        filtering = {
            "pluginId": ("exact",),
            "entityId": ("exact",),
        }
        ordering = ["id"]

    def hydrate(self, bundle):
        try:
            datafile = DataFileResource.get_via_uri(
                DataFileResource(), bundle.data["datafile"], bundle.request
            )
        except NotFound:
            datafile = DataFile.objects.get(namespace=bundle.data["datafile"])
        bundle.obj.datafile = datafile
        del bundle.data["datafile"]
        return bundle


class ExperimentParameterSetResource(ParameterSetResource):
    """API for ExperimentParameterSets"""

    experiment = fields.ForeignKey(ExperimentResource, "experiment")
    parameters = fields.ToManyField(
        "tardis.tardis_portal.api.ExperimentParameterResource",
        "experimentparameter_set",
        related_name="parameterset",
        full=True,
        null=True,
    )

    class Meta(MyTardisModelResource.Meta):
        object_class = ExperimentParameterSet
        queryset = ExperimentParameterSet.objects.all()

    def dehydrate_parameters(self, bundle):
        if has_sensitive_access(bundle.request, bundle.obj.experiment.id, "experiment"):
            return bundle.data["parameters"]
        return [
            x for x in bundle.data["parameters"] if x.obj.name.sensitive is not True
        ]


class ExperimentParameterResource(ParameterResource):
    parameterset = fields.ForeignKey(ExperimentParameterSetResource, "parameterset")

    class Meta(MyTardisModelResource.Meta):
        object_class = ExperimentParameter
        queryset = ExperimentParameter.objects.all()


class DatasetParameterSetResource(ParameterSetResource):
    dataset = fields.ForeignKey(DatasetResource, "dataset")
    parameters = fields.ToManyField(
        "tardis.tardis_portal.api.DatasetParameterResource",
        "datasetparameter_set",
        related_name="parameterset",
        full=True,
        null=True,
    )

    class Meta(MyTardisModelResource.Meta):
        object_class = DatasetParameterSet
        queryset = DatasetParameterSet.objects.all()

    def dehydrate_parameters(self, bundle):
        if has_sensitive_access(bundle.request, bundle.obj.dataset.id, "dataset"):
            return bundle.data["parameters"]
        return [
            x for x in bundle.data["parameters"] if x.obj.name.sensitive is not True
        ]


class DatasetParameterResource(ParameterResource):
    parameterset = fields.ForeignKey(DatasetParameterSetResource, "parameterset")

    class Meta(MyTardisModelResource.Meta):
        object_class = DatasetParameter
        queryset = DatasetParameter.objects.all()


class DatafileParameterSetResource(ParameterSetResource):
    datafile = fields.ForeignKey(DataFileResource, "datafile")
    parameters = fields.ToManyField(
        "tardis.tardis_portal.api.DatafileParameterResource",
        "datafileparameter_set",
        related_name="parameterset",
        full=True,
        null=True,
    )

    class Meta(MyTardisModelResource.Meta):
        object_class = DatafileParameterSet
        queryset = DatafileParameterSet.objects.all()

    def dehydrate_parameters(self, bundle):
        if has_sensitive_access(bundle.request, bundle.obj.datafile.id, "datafile"):
            return bundle.data["parameters"]
        return [
            x for x in bundle.data["parameters"] if x.obj.name.sensitive is not True
        ]


class DatafileParameterResource(ParameterResource):
    parameterset = fields.ForeignKey(DatafileParameterSetResource, "parameterset")

    class Meta(MyTardisModelResource.Meta):
        object_class = DatafileParameter
        queryset = DatafileParameter.objects.all()


class StorageBoxResource(MyTardisModelResource):
    options = fields.ToManyField(
        "tardis.tardis_portal.api.StorageBoxOptionResource",
        attribute=lambda bundle: StorageBoxOption.objects.filter(
            storage_box=bundle.obj, key__in=StorageBoxOptionResource.accessible_keys
        ),
        related_name="storage_box",
        full=True,
        null=True,
    )
    attributes = fields.ToManyField(
        "tardis.tardis_portal.api.StorageBoxAttributeResource",
        "attributes",
        related_name="storage_box",
        full=True,
        null=True,
    )

    class Meta(MyTardisModelResource.Meta):
        object_class = StorageBox
        queryset = StorageBox.objects.all()
        ordering = ["id"]


class StorageBoxOptionResource(MyTardisModelResource):
    accessible_keys = ["location"]
    storage_box = fields.ForeignKey(
        StorageBoxResource, "storage_box", related_name="options", full=False
    )

    class Meta(MyTardisModelResource.Meta):
        object_class = StorageBoxOption
        queryset = StorageBoxOption.objects.all()
        ordering = ["id"]


class StorageBoxAttributeResource(MyTardisModelResource):
    storage_box = fields.ForeignKey(
        StorageBoxResource, "storage_box", related_name="attributes", full=False
    )

    class Meta(MyTardisModelResource.Meta):
        object_class = StorageBoxAttribute
        queryset = StorageBoxAttribute.objects.all()
        ordering = ["id"]
