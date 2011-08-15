"""
managers.py

.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>

"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group

from tardis.tardis_portal.auth.localdb_auth import django_user, django_group


class OracleSafeManager(models.Manager):
    """
    Implements a custom manager which automatically defers the
    retreival of any TextField fields on calls to get_query_set. This
    is to avoid the known issue that 'distinct' calls on query_sets
    containing TextFields fail when Oracle is being used as the
    backend.
    """
    def get_query_set(self):
        from django.db import connection
        if connection.settings_dict['ENGINE'] == 'django.db.backends.oracle':
            fields = [a.attname for a in self.model._meta.fields
                      if a.db_type(connection=connection) == 'NCLOB']
            return \
                super(OracleSafeManager, self).get_query_set().defer(*fields)
        else:
            return super(OracleSafeManager, self).get_query_set()


class ExperimentManager(OracleSafeManager):
    """
    Implements a custom manager for the Experiment model which checks
    the authorisation rules for the requesting user first

    To make this work, the request must be passed to all class
    functions. The username and the group memberships are then
    resolved via the request.groups and request.user objects.

    The :py:mod:`tardis.tardis_portal.auth.AuthService` is responsible for
    filling the request.groups object.

    """

    def all(self, request):
        """
        Returns all experiments a user - either authenticated or
        anonymous - is allowed to see and search

        :param request: a HTTP Request instance
        :type request: :py:class:`django.http.HttpRequest`
        """

        # experiment is public?
        query = Q(public=True)

        # if the user is not authenticated, they will see only public
        # experiments
        if request.user.is_authenticated():
            # for which experiments does the user have read access
            # based on USER permissions?
            query |= Q(experimentacl__pluginId=django_user,
                       experimentacl__entityId=str(request.user.id),
                       experimentacl__canRead=True)\
                       & (Q(experimentacl__effectiveDate__lte=datetime.today())
                          | Q(experimentacl__effectiveDate__isnull=True))\
                       & (Q(experimentacl__expiryDate__gte=datetime.today())
                          | Q(experimentacl__expiryDate__isnull=True))

            # for which does experiments does the user have read access
            # based on GROUP permissions
            for name, group in request.groups:
                query |= Q(experimentacl__pluginId=name,
                    experimentacl__entityId=str(group),
                    experimentacl__canRead=True)\
                    & (Q(experimentacl__effectiveDate__lte=datetime.today())
                    | Q(experimentacl__effectiveDate__isnull=True))\
                    & (Q(experimentacl__expiryDate__gte=datetime.today())
                    | Q(experimentacl__expiryDate__isnull=True))

        return super(ExperimentManager, self).get_query_set().filter(
            query).distinct()


    def get(self, request, experiment_id):
        """
        Returns an experiment under the consideration of the ACL rules
        Raises PermissionDenied if the user does not have access.

        :param request: a HTTP Request instance
        :type request: :py:class:`django.http.HttpRequest`
        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string

        """
        experiment = \
            super(ExperimentManager, self).get(pk=experiment_id)

        # if the experiment is public, return it right away
        if experiment.public:
            return experiment

        # if not, is the user logged in at all?
        if not request.user.is_authenticated():
            raise PermissionDenied

        # check if there is a user based authorisation role
        query = Q(experiment=experiment,
                  pluginId=django_user,
                  entityId=str(request.user.id),
                  canRead=True)\
                  & (Q(effectiveDate__lte=datetime.today())
                     | Q(effectiveDate__isnull=True))\
                  & (Q(expiryDate__gte=datetime.today())
                     | Q(expiryDate__isnull=True))

        # and finally check all the group based authorisation roles
        for name, group in request.groups:
            query |= Q(pluginId=name,
                       entityId=str(group),
                       experiment=experiment,
                       canRead=True)\
                       & (Q(effectiveDate__lte=datetime.today())
                          | Q(effectiveDate__isnull=True))\
                       & (Q(expiryDate__gte=datetime.today())
                          | Q(expiryDate__isnull=True))

        # is there at least one ACL rule which satisfies the rules?
        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.filter(query)
        if acl.count() == 0:
            raise PermissionDenied
        else:
            return experiment

    def owned(self, request):
        """
        Return all experiments which are owned by a particular user

        :param request: a HTTP Request instance
        :type request: :py:class:`django.http.HttpRequest`

        """

        # the user must be authenticated
        if not request.user.is_authenticated():
            return []

        # build the query to filter the ACL table
        query = Q(experimentacl__pluginId=django_user,
                  experimentacl__entityId=str(request.user.id),
                  experimentacl__isOwner=True)\
                  & (Q(experimentacl__effectiveDate__lte=datetime.today())
                     | Q(experimentacl__effectiveDate__isnull=True))\
                  & (Q(experimentacl__expiryDate__gte=datetime.today())
                     | Q(experimentacl__expiryDate__isnull=True))

        return super(ExperimentManager, self).get_query_set().filter(query)

    def users(self, request, experiment_id):
        """
        returns a list of users which have ACL rules associated with
        this to this experiment

        :param request: a HTTP Request instance
        :type request: :py:class:`django.http.HttpRequest`
        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string

        """

        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.filter(pluginId=django_user,
                                   experiment__id=experiment_id,
                                   aclOwnershipType=ExperimentACL.OWNER_OWNED)
        return [User.objects.get(pk=int(a.entityId)) for a in acl]

    def user_owned_groups(self, request, experiment_id):
        """
        returns a list of user owned-groups which have ACL rules
        associated with this experiment

        :param request: a HTTP Request instance
        :type request: :py:class:`django.http.HttpRequest`
        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string

        """

        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.filter(pluginId=django_group,
                                   experiment__id=experiment_id,
                                   aclOwnershipType=ExperimentACL.OWNER_OWNED)

        return [Group.objects.get(pk=str(a.entityId)) for a in acl]

    def system_owned_groups(self, request, experiment_id):
        """
        returns a list of sytem-owned groups which have ACL rules
        associated with this experiment

        :param request: a HTTP Request instance
        :type request: :py:class:`django.http.HttpRequest`
        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string

        """

        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.filter(pluginId=django_group,
                                   experiment__id=experiment_id,
                                   aclOwnershipType=ExperimentACL.SYSTEM_OWNED)

        return [Group.objects.get(pk=str(a.entityId)) for a in acl]

    def external_users(self, request, experiment_id):
        """
        returns a list of groups which have external ACL rules

        :param request: a HTTP Request instance
        :type request: :py:class:`django.http.HttpRequest`
        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string

        """

        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.exclude(pluginId=django_user)
        acl = acl.exclude(pluginId=django_group)
        acl = acl.filter(experiment__id=experiment_id)

        if not acl:
            return None

        from tardis.tardis_portal.auth import AuthService
        authService = AuthService()

        result = []
        for a in acl:
            group = authService.searchGroups(plugin=a.pluginId,
                                             name=a.entityId)
            if group:
                result += group
        return result


class ParameterNameManager(models.Manager):
    def get_by_natural_key(self, namespace, name):
        return self.get(schema__namespace=namespace, name=name)


class SchemaManager(models.Manager):
    def get_by_natural_key(self, namespace):
        return self.get(namespace=namespace)
