"""
managers.py

.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>

"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group

from .auth.localdb_auth import django_user, django_group
from .models.access_control import ObjectACL


class OracleSafeManager(models.Manager):
    """
    Implements a custom manager which automatically defers the
    retreival of any TextField fields on calls to get_queryset. This
    is to avoid the known issue that 'distinct' calls on query_sets
    containing TextFields fail when Oracle is being used as the
    backend.
    """

    def get_queryset(self):
        from django.db import connection
        if connection.settings_dict['ENGINE'] == 'django.db.backends.oracle':
            fields = [a.attname for a in self.model._meta.fields
                      if a.db_type(connection=connection) == 'NCLOB']
            return super().get_queryset().defer(*fields)
        return super().get_queryset()


class ParameterNameManager(models.Manager):
    def get_by_natural_key(self, namespace, name):
        return self.get(schema__namespace=namespace, name=name)


class SchemaManager(models.Manager):
    def get_by_natural_key(self, namespace):
        return self.get(namespace=namespace)


class SafeManager(models.Manager):

    """
    Implements a custom manager for the Project/Experiment/Dataset/DataFile
    models which checks the authorisation rules for the requesting user first

    To make this work, the request must be passed to all class
    functions. The username and the group memberships are then
    resolved via the user.userprofile.ext_groups and user objects.

    The :py:mod:`tardis.tardis_portal.auth.AuthService` is responsible for
    filling the request.groups object.
    """

    def all(self, user, downloadable=False, viewsensitive=False):  # @ReservedAssignment
        """
        Returns all proj/exp/set/files a user - either authenticated or
        anonymous - is allowed to see and search

        :param User user: a User instance
        :returns: QuerySet of objects
        :rtype: QuerySet
        """

        query = self._query_owned_and_shared(
            user, downloadable, viewsensitive)  # self._query_all_public() |\

        return super().get_queryset().filter(
            query).distinct()

    def _query_owned(self, user, user_id=None):
        # build the query to filter the ACL table
        query = Q(objectacls__pluginId=django_user,
                  objectacls__entityId=str(user_id or user.id),
                  objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                  objectacls__isOwner=True) &\
            (Q(objectacls__effectiveDate__lte=datetime.today())
             | Q(objectacls__effectiveDate__isnull=True)) &\
            (Q(objectacls__expiryDate__gte=datetime.today())
             | Q(objectacls__expiryDate__isnull=True))
        return query

    def _query_owned_by_group(self, group, group_id=None):
        # build the query to filter the ACL table
        query = Q(objectacls__pluginId=django_group,
                  objectacls__entityId=str(group_id or group.id),
                  objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                  objectacls__isOwner=True) &\
            (Q(objectacls__effectiveDate__lte=datetime.today())
             | Q(objectacls__effectiveDate__isnull=True)) &\
            (Q(objectacls__expiryDate__gte=datetime.today())
             | Q(objectacls__expiryDate__isnull=True))
        return query

    # ARE THE TOKENS EXP ONLY?
    def _query_shared(self, user, downloadable=False, viewsensitive=False):
        '''
        get all shared proj/exp/set/files, not owned ones
        '''
        # if the user is not authenticated, only tokens apply
        # this is almost duplicate code of end of has_perm in authorisation.py
        # should be refactored, but cannot think of good way atm
        if not user.is_authenticated:
            from .auth.token_auth import TokenGroupProvider
            query = Q(id=None)
            tgp = TokenGroupProvider()
            for group in tgp.getGroups(user):
                if downloadable:
                    query |= Q(objectacls__pluginId=tgp.name,
                               objectacls__entityId=str(group),
                               objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                               objectacls__canDownload=True) &\
                        (Q(objectacls__effectiveDate__lte=datetime.today())
                         | Q(objectacls__effectiveDate__isnull=True)) &\
                        (Q(objectacls__expiryDate__gte=datetime.today())
                         | Q(objectacls__expiryDate__isnull=True))
                elif viewsensitive:
                    query |= Q(objectacls__pluginId=tgp.name,
                               objectacls__entityId=str(group),
                               objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                               objectacls__canSensitive=True) &\
                        (Q(objectacls__effectiveDate__lte=datetime.today())
                         | Q(objectacls__effectiveDate__isnull=True)) &\
                        (Q(objectacls__expiryDate__gte=datetime.today())
                         | Q(objectacls__expiryDate__isnull=True))
                else:
                    query |= Q(objectacls__pluginId=tgp.name,
                               objectacls__entityId=str(group),
                               objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                               objectacls__canRead=True) &\
                        (Q(objectacls__effectiveDate__lte=datetime.today())
                         | Q(objectacls__effectiveDate__isnull=True)) &\
                        (Q(objectacls__expiryDate__gte=datetime.today())
                         | Q(objectacls__expiryDate__isnull=True))
            return query

        # for which proj/exp/set/files does the user have read access
        # based on USER permissions?
        if downloadable:
            query = Q(objectacls__pluginId=django_user,
                      objectacls__entityId=str(user.id),
                      objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                      objectacls__canDownload=True,
                      objectacls__isOwner=False) &\
                (Q(objectacls__effectiveDate__lte=datetime.today())
                 | Q(objectacls__effectiveDate__isnull=True)) &\
                (Q(objectacls__expiryDate__gte=datetime.today())
                 | Q(objectacls__expiryDate__isnull=True))
        elif viewsensitive:
            query = Q(objectacls__pluginId=django_user,
                      objectacls__entityId=str(user.id),
                      objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                      objectacls__canSensitive=True,
                      objectacls__isOwner=False) &\
                (Q(objectacls__effectiveDate__lte=datetime.today())
                 | Q(objectacls__effectiveDate__isnull=True)) &\
                (Q(objectacls__expiryDate__gte=datetime.today())
                 | Q(objectacls__expiryDate__isnull=True))
        else:
            query = Q(objectacls__pluginId=django_user,
                      objectacls__entityId=str(user.id),
                      objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                      objectacls__canRead=True,
                      objectacls__isOwner=False) &\
                (Q(objectacls__effectiveDate__lte=datetime.today())
                 | Q(objectacls__effectiveDate__isnull=True)) &\
                (Q(objectacls__expiryDate__gte=datetime.today())
                 | Q(objectacls__expiryDate__isnull=True))
        # for which does proj/exp/set/files does the user have read access
        # based on GROUP permissions
        for name, group in user.userprofile.ext_groups:
            if downloadable:
                query |= Q(objectacls__pluginId=name,
                           objectacls__entityId=str(group),
                           objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                           objectacls__canDownload=True) &\
                    (Q(objectacls__effectiveDate__lte=datetime.today())
                     | Q(objectacls__effectiveDate__isnull=True)) &\
                    (Q(objectacls__expiryDate__gte=datetime.today())
                     | Q(objectacls__expiryDate__isnull=True))
            elif viewsensitive:
                query |= Q(objectacls__pluginId=name,
                           objectacls__entityId=str(group),
                           objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                           objectacls__canSensitive=True) &\
                    (Q(objectacls__effectiveDate__lte=datetime.today())
                     | Q(objectacls__effectiveDate__isnull=True)) &\
                    (Q(objectacls__expiryDate__gte=datetime.today())
                     | Q(objectacls__expiryDate__isnull=True))
            else:
                query |= Q(objectacls__pluginId=name,
                           objectacls__entityId=str(group),
                           objectacls__content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                           objectacls__canRead=True) &\
                    (Q(objectacls__effectiveDate__lte=datetime.today())
                     | Q(objectacls__effectiveDate__isnull=True)) &\
                    (Q(objectacls__expiryDate__gte=datetime.today())
                     | Q(objectacls__expiryDate__isnull=True))
        return query


    def _query_owned_and_shared(self, user, downloadable=False, viewsensitive=False):
        return self._query_shared(user, downloadable, viewsensitive) | self._query_owned(user)


    def owned_and_shared(self, user, downloadable=False, viewsensitive=False):
        return super().get_queryset().filter(
            self._query_owned_and_shared(user, downloadable, viewsensitive)).distinct()


    def owned(self, user):
        """
        Return all proj/exp/set/files which are owned by a particular user, including
        those shared with a group of which the user is a member.

        :param User user: a User instance
        :returns: QuerySet of proj/exp/set/files owned by user
        :rtype: QuerySet
        """

        # the user must be authenticated
        if not user.is_authenticated:
            return super().get_queryset().none()

        query = self._query_owned(user)
        for group in user.groups.all():
            query |= self._query_owned_by_group(group)
        return super().get_queryset().filter(query).distinct()


    def shared(self, user):
        return super().get_queryset().filter(
            self._query_shared(user)).distinct()


    def get(self, user, obj_id):
        """
        Returns a proj/exp/set/file under the consideration of the ACL rules
        Raises PermissionDenied if the user does not have access.

        :param User user: a User instance
        :param int obj_id: the ID of the proj/exp/set/file to be edited
        :returns: proj/exp/set/file
        :rtype: proj/exp/set/file
        :raises PermissionDenied:
        """
        obj = super().get(pk=obj_id)

        if user.has_perm('tardis_acls.view_'+self.model.get_ct(self.model).model.replace(' ',''), obj):
            return obj
        raise PermissionDenied


    def owned_by_user(self, user):
        """
        Return all proj/exp/set/files which are owned by a particular user id

        :param User user: a User Object
        :return: QuerySet of proj/exp/set/files owned by user
        :rtype: QuerySet
        """
        query = self._query_owned(user)
        return super().get_queryset().filter(query)


    def owned_by_group(self, group):
        """
        Return all proj/exp/set/files that are owned by a particular group
        """
        query = self._query_owned_by_group(group)
        return super().get_queryset().filter(query)


    def owned_by_user_id(self, userId):
        """
        Return all proj/exp/set/files which are owned by a particular user id

        :param int userId: a User ID
        :returns: QuerySet of proj/exp/set/files owned by user id
        :rtype: QuerySet
        """
        query = self._query_owned(user=None, user_id=userId)
        return super().get_queryset().filter(query)


    def user_acls(self, obj_id):
        """
        Returns a list of ACL rules associated with this proj/exp/set/file.

        :param experiment_id: the ID of the proj/exp/set/file
        :type experiment_id: string
        :returns: QuerySet of ACLs
        :rtype: QuerySet
        """
        obj = super().get(pk=obj_id)

        return ObjectACL.objects.filter(
            pluginId=django_user,
            content_type=self.model.get_ct(self.model),
            object_id=obj_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)


    def users(self, obj_id):
        """
        Returns a list of users who have ACL rules associated with this
        proj/exp/set/file.

        :param int obj_id: the ID of the proj/exp/set/file
        :returns: QuerySet of Users with proj/exp/set/file access
        :rtype: QuerySet
        """
        acl = self.user_acls(obj_id)
        return User.objects.filter(pk__in=[int(a.entityId) for a in acl])

    def group_acls(self, obj_id):
        """
        Returns a list of ACL rules associated with this proj/exp/set/file.

        :param experiment_id: the ID of the proj/exp/set/file
        :type experiment_id: string
        :returns: QuerySet of ACLs
        :rtype: QuerySet
        """
        obj = super().get(pk=obj_id)

        return ObjectACL.objects.filter(
            pluginId=django_group,
            content_type=self.model.get_ct(self.model),
            object_id=obj_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)

    def groups(self, obj_id):
        """
        Returns a list of users who have ACL rules associated with this
        proj/exp/set/file.

        :param int obj_id: the ID of the proj/exp/set/file
        :returns: QuerySet of Users with proj/exp/set/file access
        :rtype: QuerySet
        """
        acl = self.group_acls(obj_id)
        return Group.objects.filter(pk__in=[int(a.entityId) for a in acl])

    def user_owned_groups(self, obj_id):
        """
        returns a list of user owned-groups which have ACL rules
        associated with this proj/exp/set/file

        :param int obj_id: the ID of the proj/exp/set/file to be edited
        :returns: QuerySet of non system Groups
        :rtype: QuerySet
        """

        acl = ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
            object_id=obj_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)

        return Group.objects.filter(pk__in=[str(a.entityId) for a in acl])


    def group_acls_user_owned(self, obj_id):
        """
        Returns a list of ACL rules associated with this proj/exp/set/file.

        :param int obj_id: the ID of the proj/exp/set/file
        :returns: QuerySet of ACLs
        :rtype: QuerySet
        """
        return ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
            object_id=obj_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)

    def group_acls_system_owned(self, obj_id):
        """
        Returns a list of ACL rules associated with this proj/exp/set/file.

        :param int obj_id: the ID of the proj/exp/set/file
        :returns: QuerySet of system-owned ACLs for proj/exp/set/file
        :rtype: QuerySet
        """
        return ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
            object_id=obj_id,
            aclOwnershipType=ObjectACL.SYSTEM_OWNED)


    def system_owned_groups(self, obj_id):
        """
        returns a list of sytem-owned groups which have ACL rules
        associated with this proj/exp/set/file

        :param obj_id: the ID of the proj/exp/set/file to be edited
        :type obj_id: string
        :returns: system owned groups for proj/exp/set/file
        :rtype: QuerySet
        """
        acl = ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
            object_id=obj_id,
            aclOwnershipType=ObjectACL.SYSTEM_OWNED)

        return Group.objects.filter(pk__in=[str(a.entityId) for a in acl])


    def external_users(self, obj_id):
        """
        returns a list of groups which have external ACL rules

        :param int obj_id: the ID of the proj/exp/set/file to be edited
        :returns: list of groups with external ACLs
        :rtype: list
        """

        from .models import ObjectACL
        acl = ObjectACL.objects.exclude(pluginId=django_user)
        acl = acl.exclude(pluginId='django_group')
        acl = acl.filter(content_type__model=self.model.get_ct(self.model).model.replace(' ',''),
                         object_id=obj_id)

        if not acl:
            return None

        from .auth import AuthService
        authService = AuthService()

        result = []
        for a in acl:
            group = authService.searchGroups(plugin=a.pluginId,
                                             name=a.entityId)
            if group:
                result += group
        return result


    # Experiment only so far
    def public(self):
        query = self._query_all_public()
        return super().get_queryset().filter(
            query).distinct()


    # Experiment only so far
    def _query_all_public(self):
        from .models import Experiment
        return ~Q(public_access=Experiment.PUBLIC_ACCESS_NONE) &\
               ~Q(public_access=Experiment.PUBLIC_ACCESS_EMBARGO)
