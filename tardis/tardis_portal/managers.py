"""
managers.py
.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>
.. moduleauthor::  Mike Laverick <mikelaverick@btinternet.com>

"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from django.db.models import Prefetch


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
    Implements a custom manager for the Experiment/Dataset/Datafile model
    which checks the authorisation rules for the requesting user first

    To make this work, the request must be passed to all class
    functions. The username and the group memberships are then
    resolved via the user.userprofile.ext_groups and user objects.

    The :py:mod:`tardis.tardis_portal.auth.AuthService` is responsible for
    filling the request.groups object.

    The "get, owned, shared, owned_and_shared, public, all" functions return
    distinct querysets of experiments/datasets/datafiles ready to be used elsewhere
    in my tardis. They invoke one or more of the underscore functions that build
    the appropriate Django query.

    The underscore functions "_query_owned, _query_owned_by_group, _query_shared,
    _query_owned_and_shared, _query_all_public" are modular queries that can be
    combined together using Django query logic, and do not call the distinct()
    Django function which normally is only called at the end of a chain of queries
    (such as in the get/owned/shared/owned_and_shared/public/all functions).

    The remaining functions are used to return various querysets of
    users/groups/tokens/acls pertaining to a given experiment/dataset/datafile.
    """

    # To ensure compatability with Oracle backends, while avoiding an additional
    # level of manager subclassing
    def get_queryset(self):
        from django.db import connection
        if connection.settings_dict['ENGINE'] == 'django.db.backends.oracle':
            fields = [a.attname for a in self.model._meta.fields
                      if a.db_type(connection=connection) == 'NCLOB']
            return super().get_queryset().defer(*fields)
        return super().get_queryset()


    def get(self, user, obj_id):
        """
        Returns an experiment/dataset/datafile under the consideration of the
        ACL rules. Raises PermissionDenied if the user does not have access.

        :param User user: a User instance
        :param int experiment_id: the ID of the exp/set/file to be edited
        :returns: Experiment/Dataset/DataFile
        :rtype: Experiment/Dataset/DataFile
        :raises PermissionDenied:
        """
        obj = super().get(pk=obj_id)
        if user.has_perm('tardis_acls.view_'+self.model.get_ct(self.model
                                                ).model.replace(' ',''), obj):
            return obj
        raise PermissionDenied


    def owned(self, user):
        """
        Return all experiments/datasets/datafiles which are owned by a
        particular user, including those owned by a group of which the user
        is a member.
        :param User user: a User instance
        :returns: QuerySet of exp/set/files owned by user
        :rtype: QuerySet
        """
        # the user must be authenticated
        if not user.is_authenticated:
            return super().get_queryset().none()
        query = self._query_owned(user)
        for group in user.groups.all():
            query |= self._query_owned_by_group(group)
        return query.distinct()


    def shared(self, user):
        """
        Return all experiments/datasets/datafiles which are shared with a
        particular user via group membership.
        :param User user: a User instance
        :returns: QuerySet of exp/set/files shared with user
        :rtype: QuerySet
        """
        return self._query_shared(user).distinct()


    def owned_and_shared(self, user):
        """
        Return all experiments/datasets/datafiles which are either owned by or
        shared with a particular user, including those owned by a group of which
        the user is a member. This function omits publicly accessible experiments.
        :param User user: a User instance
        :returns: QuerySet of exp/set/files owned by or shared with a user
        :rtype: QuerySet
        """
        return self._query_owned_and_shared(user).distinct()


    def public(self):
        """
        Return all experiments/datasets/datafiles which are publicly available.
        :param User user: a User instance
        :returns: QuerySet of exp/set/files that are publicly available
        :rtype: QuerySet
        """
        return self._query_all_public().distinct()


    def all(self, user):  # @ReservedAssignment
        """
        Return all experiments/datasets/datafiles that are available to a user,
        including owned, shared, and public objects.
        :param User user: a User instance
        :returns: QuerySet of all exp/set/files accessible to the user
        :rtype: QuerySet
        """
        query = self._query_all_public() | self._query_owned_and_shared(user)
        return query.distinct()


    def _query_on_acls(self, user=None, group=None, token=None, isOwner=False):
        filter_dict = {}
        exclude_dict = {}
        if self.model.get_ct(self.model).model == "experiment":
            from .models import Experiment, ExperimentACL
            OBJECT = Experiment
            OBJECTACL = ExperimentACL
            acl_str = "experimentacl"
        if self.model.get_ct(self.model).model == "dataset":
            from .models import Dataset, DatasetACL
            OBJECT = Dataset
            OBJECTACL = DatasetACL
            acl_str = "datasetacl"
        if self.model.get_ct(self.model).model == "datafile":
            from .models import DataFile, DatafileACL
            OBJECT = DataFile
            OBJECTACL = DatafileACL
            acl_str = "datafileacl"

        if not any([user, group, token, isOwner]):
            return OBJECT.objects.none()

        if user:
            related = "user"
            filter_dict[acl_str+"__user"] = user
        elif group:
            related = "group"
            filter_dict[acl_str+"__group"] = group
        elif token:
            related = "token"
            filter_dict[acl_str+"__token"] = token

        if isOwner:
            filter_dict[acl_str+"__isOwner"] = True
        else:
            filter_dict[acl_str+"__isOwner"] = False

        exclude_dict[acl_str+"__effectiveDate__gte"] = datetime.today()
        exclude_dict[acl_str+"__expiryDate__lte"] = datetime.today()

        query = OBJECT.objects.prefetch_related(Prefetch(acl_str+"_set",
                             queryset=OBJECTACL.objects.select_related(related))
                                 ).filter(**filter_dict).exclude(**exclude_dict)
        return query


    def _query_owned(self, user, user_id=None):
        if user_id is not None:
            user = User.objects.get(pk=user_id)
        if user.id is None:
            return super().get_queryset().none()
        query = self._query_on_acls(user=user, isOwner=True)
        return query


    def _query_owned_by_group(self, group, group_id=None):
        if group_id is not None:
            group = Group.objects.get(pk=group_id)
        if group.id is None:
            return super().get_queryset().none()
        query = self._query_on_acls(group=group, isOwner=True)
        return query


    def _query_shared(self, user):
        '''
        get all shared proj/exp/set/files, not owned ones
        '''
        # if the user is not authenticated, only tokens apply
        # this is almost duplicate code of end of has_perm in authorisation.py
        # should be refactored, but cannot think of good way atm
        if not user.is_authenticated:
            from .auth.token_auth import TokenGroupProvider

            query = self._query_on_acls()
            tgp = TokenGroupProvider()
            for token in tgp.getGroups(user):
                query |= self._query_on_acls(token=token)
            return query
        # for which proj/exp/set/files does the user have read access
        # based on USER permissions?
        query = self._query_on_acls(user=user)
        # for which does proj/exp/set/files does the user have read access
        # based on GROUP permissions
        for group in user.groups.all():
            query |= self._query_on_acls(group=group)
        return query


    def _query_owned_and_shared(self, user):
        return self._query_shared(user) | self._query_owned(user)


    def _query_all_public(self):
        if self.model.get_ct(self.model).model == "experiment":
            from .models import Experiment
            query = Experiment.objects.filter(public_access=Experiment.PUBLIC_ACCESS_NONE)
            query |= Experiment.objects.filter(public_access=Experiment.PUBLIC_ACCESS_EMBARGO)
            return query
        # Dataset does not have a "public" functionality on a Micro-level yet
        elif self.model.get_ct(self.model).model == "dataset":
            from .models import Dataset
            return Dataset.objects.none()
        # DataFile does not have a "public" functionality on a Micro-level yet
        elif self.model.get_ct(self.model).model == "datafile":
            from .models import DataFile
            return DataFile.objects.none()


    def owned_by_user(self, user):
        """
        Return all exps/sets/files which are owned by a particular user id

        :param User user: a User Object
        :return: QuerySet of exps/sets/files owned by user
        :rtype: QuerySet
        """
        query = self._query_owned(user)
        return query


    def owned_by_group(self, group):
        """
        Return all exps/sets/files that are owned by a particular group
        """
        query = self._query_owned_by_group(group)
        return query


    def owned_by_user_id(self, userId):
        """
        Return all exps/sets/files which are owned by a particular user id

        :param int userId: a User ID
        :returns: QuerySet of exps/sets/files owned by user id
        :rtype: QuerySet
        """
        query = self._query_owned(user=None, user_id=userId)
        return query


    def user_acls(self, obj_id):
        """
        Returns a list of ACL rules associated with this exp/set/file.
        :param obj_id: the ID of the exp/set/file
        :type obj_id: string
        :returns: QuerySet of ACLs
        :rtype: QuerySet
        """
        obj = super().get(pk=obj_id)
        if self.model.get_ct(self.model).model == "experiment":
            from .models.access_control import ExperimentACL
            return obj.experimentacl_set.select_related("user").filter(user__isnull=False,
                                             aclOwnershipType=ExperimentACL.OWNER_OWNED)
        if self.model.get_ct(self.model).model == "dataset":
            from .models.access_control import DatasetACL
            return obj.datasetacl_set.select_related("user").filter(user__isnull=False,
                                             aclOwnershipType=DatasetACL.OWNER_OWNED)
        if self.model.get_ct(self.model).model.replace(" ","") == "datafile":
            from .models.access_control import DatafileACL
            return obj.datafileacl_set.select_related("user").filter(user__isnull=False,
                                             aclOwnershipType=DatafileACL.OWNER_OWNED)
        return super().get_queryset().none()


    def users(self, obj_id):
        """
        Returns a list of users who have ACL rules associated with this
        exp/set/file.

        :param int experiment_id: the ID of the exp/set/file
        :returns: QuerySet of Users with exp/set/file access
        :rtype: QuerySet
        """
        acl = self.user_acls(obj_id)
        return User.objects.filter(pk__in=[int(a.user.id) for a in acl])


    def group_acls(self, obj_id):
        """
        Returns a list of ACL rules associated with this exp/set/file.
        :param obj_id: the ID of the exp/set/file
        :type obj_id: string
        :returns: QuerySet of ACLs
        :rtype: QuerySet
        """
        from .models.access_control import (ExperimentACL, DatasetACL, DatafileACL)
        obj = super().get(pk=obj_id)
        if self.model.get_ct(self.model).model == "experiment":
            return obj.experimentacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=ExperimentACL.OWNER_OWNED)
        if self.model.get_ct(self.model).model == "dataset":
            return obj.datasetacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatasetACL.OWNER_OWNED)
        if self.model.get_ct(self.model).model.replace(" ","") == "datafile":
            return obj.datafileacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatafileACL.OWNER_OWNED)
        return super().get_queryset().none()


    def groups(self, obj_id):
        """
        Returns a list of groups who have ACL rules associated with this
        exp/set/file.

        :param int experiment_id: the ID of the exp/set/file
        :returns: QuerySet of Groups with exp/set/file access
        :rtype: QuerySet
        """
        acl = self.group_acls(obj_id)
        return Group.objects.filter(pk__in=[int(a.group.id) for a in acl])


    def user_owned_groups(self, obj_id):
        """
        returns a list of user owned-groups which have ACL rules
        associated with this exp/set/file
        :param int obj_id: the ID of the exp/set/file to be edited
        :returns: QuerySet of non system Groups
        :rtype: QuerySet
        """
        from .models.access_control import (ExperimentACL, DatasetACL, DatafileACL)
        obj = super().get(pk=obj_id)
        if self.model.get_ct(self.model).model == "experiment":
            acl = obj.experimentacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=ExperimentACL.OWNER_OWNED)
        if self.model.get_ct(self.model).model == "dataset":
            acl = obj.datasetacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatasetACL.OWNER_OWNED)
        if self.model.get_ct(self.model).model.replace(" ","") == "datafile":
            acl = obj.datafileacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatafileACL.OWNER_OWNED)

        return Group.objects.filter(pk__in=[str(a.group.id) for a in acl])


    def group_acls_user_owned(self, obj_id):
        """
        Returns a list of ACL rules associated with this exp/set/file.
        :param int obj_id: the ID of the exp/set/file
        :returns: QuerySet of ACLs
        :rtype: QuerySet
        """
        from .models.access_control import (ExperimentACL, DatasetACL, DatafileACL)
        obj = super().get(pk=obj_id)
        if self.model.get_ct(self.model).model == "experiment":
            return obj.experimentacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=ExperimentACL.OWNER_OWNED)
        if self.model.get_ct(self.model).model == "dataset":
            return obj.datasetacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatasetACL.OWNER_OWNED)
        if self.model.get_ct(self.model).model.replace(" ","") == "datafile":
            return obj.datafileacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatafileACL.OWNER_OWNED)
        return super().get_queryset().none()


    def group_acls_system_owned(self, obj_id):
        """
        Returns a list of ACL rules associated with this exp/set/file.
        :param int obj_id: the ID of the exp/set/file
        :returns: QuerySet of system-owned ACLs for exp/set/file
        :rtype: QuerySet
        """
        from .models.access_control import (ExperimentACL, DatasetACL, DatafileACL)
        obj = super().get(pk=obj_id)
        if self.model.get_ct(self.model).model == "experiment":
            return obj.experimentacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=ExperimentACL.SYSTEM_OWNED)
        if self.model.get_ct(self.model).model == "dataset":
            return obj.datasetacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatasetACL.SYSTEM_OWNED)
        if self.model.get_ct(self.model).model.replace(" ","") == "datafile":
            return obj.datafileacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatafileACL.SYSTEM_OWNED)
        return super().get_queryset().none()


    def system_owned_groups(self, obj_id):
        """
        returns a list of sytem-owned groups which have ACL rules
        associated with this proj/exp/set/file
        :param obj_id: the ID of the proj/exp/set/file to be edited
        :type obj_id: string
        :returns: system owned groups for proj/exp/set/file
        :rtype: QuerySet
        """
        from .models.access_control import (ExperimentACL, DatasetACL, DatafileACL)
        obj = super().get(pk=obj_id)
        if self.model.get_ct(self.model).model == "experiment":
            acl = obj.experimentacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=ExperimentACL.SYSTEM_OWNED)
        if self.model.get_ct(self.model).model == "dataset":
            acl = obj.datasetacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatasetACL.SYSTEM_OWNED)
        if self.model.get_ct(self.model).model.replace(" ","") == "datafile":
            acl = obj.datafileacl_set.select_related("group").filter(group__isnull=False,
                                             aclOwnershipType=DatafileACL.SYSTEM_OWNED)
        return Group.objects.filter(pk__in=[str(a.group.id) for a in acl])


    def external_users(self, obj_id):
        """
        returns a list of groups which have external ACL rules
        :param int obj_id: the ID of the /exp/set/file to be edited
        :returns: list of groups with external ACLs
        :rtype: list
        """
        obj = super().get(pk=obj_id)
        if self.model.get_ct(self.model).model == "experiment":
            acl = obj.experimentacl_set.select_related("token").filter(token__isnull=False)
        if self.model.get_ct(self.model).model == "dataset":
            acl = obj.datasetacl_set.select_related("token").filter(token__isnull=False)
        if self.model.get_ct(self.model).model.replace(" ","") == "datafile":
            acl = obj.datafileacl_set.select_related("token").filter(token__isnull=False)

        if not acl:
            return None

        from .auth import AuthService
        authService = AuthService()

        result = []
        for a in acl:
            group = authService.searchGroups(plugin=u'token_group',
                                             name=acl.experiment.id)
            if group:
                result += group
        return result
