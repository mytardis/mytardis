"""
managers.py

.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>

"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group

from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.models import ObjectACL


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
    resolved via the user.get_profile().ext_groups and user objects.

    The :py:mod:`tardis.tardis_portal.auth.AuthService` is responsible for
    filling the request.groups object.

    """

    def all(self, user):  # @ReservedAssignment
        """
        Returns all experiments a user - either authenticated or
        anonymous - is allowed to see and search

        :param user: a User instance
        :type request: :py:class:`django.http.HttpRequest`
        """

        query = self._query_all_public() |\
            self._query_owned_and_shared(user)

        return super(ExperimentManager, self).get_query_set().filter(
            query).distinct()

    def owned_and_shared(self, user):
        return super(ExperimentManager, self).get_query_set().filter(
            self._query_owned_and_shared(user)).distinct()

    def _query_owned_and_shared(self, user):
        # if the user is not authenticated, only tokens apply
        # this is almost duplicate code of end of has_perm in authorisation.py
        # should be refactored, but cannot think of good way atm
        if not user.is_authenticated():
            from tardis.tardis_portal.auth.token_auth import TokenGroupProvider
            query = Q(id=None)
            tgp = TokenGroupProvider()
            for group in tgp.getGroups(user):
                query |= Q(objectacls__pluginId=tgp.name,
                           objectacls__entityId=str(group),
                           objectacls__canRead=True) &\
                    (Q(objectacls__effectiveDate__lte=datetime.today())
                     | Q(objectacls__effectiveDate__isnull=True)) &\
                    (Q(objectacls__expiryDate__gte=datetime.today())
                     | Q(objectacls__expiryDate__isnull=True))
            return query

        # for which experiments does the user have read access
        # based on USER permissions?
        query = Q(objectacls__pluginId=django_user,
                  objectacls__entityId=str(user.id),
                  objectacls__canRead=True) &\
            (Q(objectacls__effectiveDate__lte=datetime.today())
             | Q(objectacls__effectiveDate__isnull=True)) &\
            (Q(objectacls__expiryDate__gte=datetime.today())
             | Q(objectacls__expiryDate__isnull=True))

        # for which does experiments does the user have read access
        # based on GROUP permissions
        for name, group in user.get_profile().ext_groups:
            query |= Q(objectacls__pluginId=name,
                       objectacls__entityId=str(group),
                       objectacls__canRead=True) &\
                (Q(objectacls__effectiveDate__lte=datetime.today())
                 | Q(objectacls__effectiveDate__isnull=True)) &\
                (Q(objectacls__expiryDate__gte=datetime.today())
                 | Q(objectacls__expiryDate__isnull=True))
        return query

    def _query_all_public(self):
        from tardis.tardis_portal.models import Experiment
        return ~Q(public_access=Experiment.PUBLIC_ACCESS_NONE)

    def get(self, user, experiment_id):
        """
        Returns an experiment under the consideration of the ACL rules
        Raises PermissionDenied if the user does not have access.

        :param user: a User instance
        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string

        """
        experiment = \
            super(ExperimentManager, self).get(pk=experiment_id)

        if user.has_perm('tardis_acls.view_experiment', experiment):
            return experiment
        else:
            raise PermissionDenied

    def owned(self, user):
        """
        Return all experiments which are owned by a particular user

        :param request: a HTTP Request instance
        :type request: :py:class:`django.http.HttpRequest`

        """

        # the user must be authenticated
        if not user.is_authenticated():
            return super(ExperimentManager, self).get_empty_query_set()

        return self.owned_by_user_id(user.id)

    def owned_by_user_id(self, userId):
        """
        Return all experiments which are owned by a particular user id

        :param userId: a User ID
        :type userId: integer

        """
        # build the query to filter the ACL table
        query = Q(objectacls__pluginId=django_user,
                  objectacls__entityId=str(userId),
                  objectacls__isOwner=True) &\
            (Q(objectacls__effectiveDate__lte=datetime.today())
             | Q(objectacls__effectiveDate__isnull=True)) &\
            (Q(objectacls__expiryDate__gte=datetime.today())
             | Q(objectacls__expiryDate__isnull=True))

        return super(ExperimentManager, self).get_query_set().filter(query)

    def user_acls(self, experiment_id):
        """
        Returns a list of ACL rules associated with this experiment.

        :param experiment_id: the ID of the experiment
        :type experiment_id: string

        """
        experiment = \
            super(ExperimentManager, self).get(pk=experiment_id)

        return ObjectACL.objects.filter(
            pluginId=django_user,
            content_type=experiment.get_ct(),
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)

    def users(self, experiment_id):
        """
        Returns a list of users who have ACL rules associated with this
        experiment.

        :param experiment_id: the ID of the experiment
        :type experiment_id: string

        """
        acl = self.user_acls(experiment_id)
        return User.objects.filter(pk__in=[int(a.entityId) for a in acl])

    def user_owned_groups(self, experiment_id):
        """
        returns a list of user owned-groups which have ACL rules
        associated with this experiment

        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string

        """

        acl = ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__name='experiment',
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)

        return Group.objects.filter(pk__in=[str(a.entityId) for a in acl])

    def group_acls_user_owned(self, experiment_id):
        """
        Returns a list of ACL rules associated with this experiment.

        :param experiment_id: the ID of the experiment
        :type experiment_id: string

        """
        return ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__name='experiment',
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)

    def group_acls_system_owned(self, experiment_id):
        """
        Returns a list of ACL rules associated with this experiment.

        :param experiment_id: the ID of the experiment
        :type experiment_id: string

        """
        return ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__name='experiment',
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.SYSTEM_OWNED)

    def system_owned_groups(self, experiment_id):
        """
        returns a list of sytem-owned groups which have ACL rules
        associated with this experiment

        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string

        """
        from tardis.tardis_portal.models import ObjectACL
        acl = ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__name='experiment',
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.SYSTEM_OWNED)

        return Group.objects.filter(pk__in=[str(a.entityId) for a in acl])

    def external_users(self, experiment_id):
        """
        returns a list of groups which have external ACL rules

        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string

        """

        from tardis.tardis_portal.models import ObjectACL
        acl = ObjectACL.objects.exclude(pluginId=django_user)
        acl = acl.exclude(pluginId='django_group')
        acl = acl.filter(content_type__name='experiment',
                         object_id=experiment_id)

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

    def get_by_natural_key(self, title, username):
        """ 
        Added by Sindhu Emilda for natural key support for model Experiment
        """
        return self.get_query_set.get(title=title,
                        created_by=User.objects.get_by_natural_key(username)
        )
        
class ParameterNameManager(models.Manager):
    def get_by_natural_key(self, namespace, name):
        return self.get(schema__namespace=namespace, name=name)


class SchemaManager(models.Manager):
    def get_by_natural_key(self, namespace):
        return self.get(namespace=namespace)
