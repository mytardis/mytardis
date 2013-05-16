'''
RESTful API for MyTardis models and data.
Implemented with Tastypie.

Author: Grischa Meyer
'''
from django.contrib.auth.models import User

from tardis.tardis_portal.auth.decorators import has_delete_permissions
from tardis.tardis_portal.auth.decorators import has_experiment_access
from tardis.tardis_portal.auth.decorators import has_write_permissions
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.models import ExperimentACL
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import ExperimentParameter
from tardis.tardis_portal.models.parameters import ExperimentParameterSet
from tardis.tardis_portal.models.parameters import ParameterName
from tardis.tardis_portal.models.parameters import Schema

from tastypie import fields
from tastypie.authentication import BasicAuthentication, MultiAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie.resources import ModelResource

import json as simplejson
from django.core.serializers import json
from tastypie.serializers import Serializer


class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return simplejson.dumps(data, cls=json.DjangoJSONEncoder,
                                sort_keys=True, ensure_ascii=False,
                                indent=self.json_indent) + "\n"

from django.conf import settings
if settings.DEBUG:
    default_serializer = PrettyJSONSerializer()
else:
    default_serializer = Serializer()

default_authentication = MultiAuthentication(BasicAuthentication())


class ACLAuthorization(Authorization):
    '''Authorisation class for Tastypie.
    Currently works for:
      - Experiments
    In the future, either rename this to ExperimentAuth and create many
    classes or make this one the master-auth class.

    Listed are all methods. The unused ones raise NotImplementedError.
    '''
    def read_list(self, object_list, bundle):
        if type(bundle.obj) == Experiment:
            return type(bundle.obj).safe.all(bundle.request)
        else:
            return object_list

    def read_detail(self, object_list, bundle):
        if type(bundle.obj) == Experiment:
            return has_experiment_access(bundle.request, bundle.obj.id)
        elif type(bundle.obj) == User:
            # allow all authenticated users to read user list
            return bundle.request.user.is_authenticated()
        elif type(bundle.obj) == ExperimentParameterSet:
            return True # has_experiment_access(
#                bundle.request, bundle.obj.experiment.id)
        elif type(bundle.obj) == Schema:
            return bundle.request.user.is_authenticated()
        elif type(bundle.obj) == ParameterName:
            return bundle.request.user.is_authenticated()
        elif type(bundle.obj) == ExperimentParameter:
            return bundle.request.user.is_authenticated()
        raise NotImplementedError(type(bundle.obj))

    def create_list(self, object_list, bundle):
        raise NotImplementedError(type(bundle.obj))

    def create_detail(self, object_list, bundle):
        if type(bundle.obj) == Experiment:
            return bundle.request.user.has_perm('tardis_portal.add_experiment')
        elif type(bundle.obj) == ExperimentParameterSet:
            return bundle.request.user.has_perm(
                'tardis_portal.change_experiment') # and \
#                has_write_permissions(bundle.request, bundle.obj.experiment.id)
        elif type(bundle.obj) == ExperimentParameter:
            return bundle.request.user.has_perm(
                'tardis_portal.change_experiment')
        raise NotImplementedError(type(bundle.obj))

    def update_list(self, object_list, bundle):
        allowed = []

        # Since they may not all be saved, iterate over them.
        for obj in object_list:
            if obj.user == bundle.request.user:
                allowed.append(obj)

        return allowed

    def update_detail(self, object_list, bundle):
        if type(bundle.obj) == Experiment:
            return bundle.request.user.has_perm(
                'tardis_portal.change_experiment') and \
                has_write_permissions(bundle.request, bundle.obj.id)
        elif type(bundle.obj) == Schema:
            return bundle.request.user.is_authenticated()
        elif type(bundle.obj) == ExperimentParameterSet:
            return bundle.request.user.has_perm(
                'tardis_portal.change_experiment')# and \
          #      has_write_permissions(bundle.request, bundle.obj.experiment.id)
        elif type(bundle.obj) == ExperimentParameter:
            return bundle.request.user.has_perm(
                'tardis_portal.change_experiment')
        raise NotImplementedError(type(bundle.obj))

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you!
        raise Unauthorized("Sorry, no deletes.")

    def delete_detail(self, object_list, bundle):
        if type(bundle.obj) == Experiment:
            return bundle.request.user.has_perm(
                'tardis_portal.change_experiment') and \
                has_delete_permissions(bundle.request, bundle.obj.id)
        raise Unauthorized("Sorry, no deletes.")


def lookup_by_unique_id_only(resource):
    '''
    returns custom lookup function. initialise with resource type
    '''
    def lookup_kwargs_with_identifiers(self, bundle, kwargs):
        if 'id' not in kwargs and 'pk' not in kwargs:
            # new instance is required
            return {'id': -1}  # this will not match any exisitng resource
        return super(resource,
                     self).lookup_kwargs_with_identifiers(bundle, kwargs)

    return lookup_kwargs_with_identifiers


class UserResource(ModelResource):
    class Meta:
        authentication = default_authentication
        authorization = ACLAuthorization()
        queryset = User.objects.all()
        allowed_methods = ['get']
        fields = ['username', 'first_name', 'last_name']
        serializer = default_serializer


class MyTardisModelResource(ModelResource):

    def lookup_kwargs_with_identifiers(self, bundle, kwargs):
        return lookup_by_unique_id_only(MyTardisModelResource)(
            self, bundle, kwargs)

    class Meta:
        authentication = default_authentication
        authorization = ACLAuthorization()
        serializer = default_serializer


class SchemaResource(ModelResource):

    def lookup_kwargs_with_identifiers(self, bundle, kwargs):
        return lookup_by_unique_id_only(SchemaResource)(self, bundle, kwargs)

    class Meta:
        queryset = Schema.objects.all()
        authentication = default_authentication
        authorization = ACLAuthorization()
        serializer = default_serializer


class ParameterNameResource(ModelResource):
    schema = fields.ForeignKey(SchemaResource, 'schema')

    def lookup_kwargs_with_identifiers(self, bundle, kwargs):
        return lookup_by_unique_id_only(ParameterNameResource)(
            self, bundle, kwargs)

    class Meta:
        queryset = ParameterName.objects.all()
        authentication = default_authentication
        authorization = ACLAuthorization()
        serializer = default_serializer


class ExperimentParameterSetResource(ModelResource):
    '''API for ExperimentParameterSets
    '''
    experiment = fields.ForeignKey(
        'tardis.tardis_portal.api.ExperimentResource', 'experiment')
    schema = fields.ForeignKey(SchemaResource, 'schema', full=True)
    parameters = fields.ToManyField(
        'tardis.tardis_portal.api.ExperimentParameterResource',
        'experimentparameter_set',
        related_name='parameterset', full=True)

    def lookup_kwargs_with_identifiers(self, bundle, kwargs):
        return lookup_by_unique_id_only(ExperimentParameterSetResource)(
            self, bundle, kwargs)

    class Meta:
        queryset = ExperimentParameterSet.objects.all()
        authentication = default_authentication
        authorization = ACLAuthorization()
        serializer = default_serializer


class ExperimentParameterResource(ModelResource):
    name = fields.ForeignKey(ParameterNameResource, 'name')
    parameterset = fields.ForeignKey(ExperimentParameterSetResource,
                                     'parameterset')

    def lookup_kwargs_with_identifiers(self, bundle, kwargs):
        return lookup_by_unique_id_only(ExperimentParameterResource)(
            self, bundle, kwargs)

    class Meta:
        queryset = ExperimentParameter.objects.all()
        authentication = default_authentication
        authorization = ACLAuthorization()
        serializer = default_serializer


class ExperimentResource(ModelResource):
    '''API for Experiments
    also creates a default ACL and allows ExperimentParameterSets to be read
    and written.

    TODO: catch duplicate schema submissions for parameter sets
    '''
    created_by = fields.ForeignKey(UserResource, 'created_by')
    parameter_sets = fields.ToManyField(
        ExperimentParameterSetResource,
        'experimentparameterset_set',
        related_name='experiment',
        full=True, null=True)

    def lookup_kwargs_with_identifiers(self, bundle, kwargs):
        return lookup_by_unique_id_only(ExperimentResource)(
            self, bundle, kwargs)

    class Meta:
        queryset = Experiment.objects.all()
        authentication = default_authentication
        authorization = ACLAuthorization()
        serializer = default_serializer

    def obj_create(self, bundle, **kwargs):
        '''experiments need at least one ACL to be available through the
        ExperimentManager (Experiment.safe)
        Currently not tested for failed db transactions as sqlite does not
        enforce limits.
        '''
        user = bundle.request.user
        bundle.data['created_by'] = user
        bundle = super(ExperimentResource, self).obj_create(bundle, **kwargs)
        if getattr(bundle.obj, 'id', False):
            experiment = bundle.obj
            # TODO: unify this with the view function's ACL creation,
            # maybe through an ACL toolbox.
            acl = ExperimentACL(experiment=experiment,
                                pluginId=django_user,
                                entityId=str(bundle.request.user.id),
                                canRead=True,
                                canWrite=True,
                                canDelete=True,
                                isOwner=True,
                                aclOwnershipType=ExperimentACL.OWNER_OWNED)
            acl.save()
        return bundle
