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


    def _query_on_acls(MODEL, ENTITY, ):
        # MDOEL = Experiment, Dataset, DataFile
        # ENTITY = User, Group, Token
        # TODO MAKE GENERAL FUNCTION FOR QUERIES

    query = DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("user"))
                                        ).filter(datafileacl__user=user,
                                                 datafileacl__isOwner=True,
                                                 ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                           datafileacl__expiryDate__lte=datetime.today()
                                                           )
    query = DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("user"))
                                        ).filter(datafileacl__user=user,
                                                 datafileacl__isOwner=False,
                                                 ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                           datafileacl__expiryDate__lte=datetime.today()
                                                           )
    query = DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("group"))
                                        ).filter(datafileacl__group=group,
                                                 datafileacl__isOwner=True,
                                                 ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                           datafileacl__expiryDate__lte=datetime.today()
                                                           )
    query |= DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("group"))
                                        ).filter(datafileacl__group=group,
                                                 datafileacl__isOwner=False,
                                                 ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                           datafileacl__expiryDate__lte=datetime.today()
                                                           )
    query |= DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("token"))
                                        ).filter(datafileacl__token=token,
                                                 datafileacl__isOwner=False,
                                                 ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                           datafileacl__expiryDate__lte=datetime.today()
                                                           )

    def _query_owned(self, user, user_id=None):
        if user_id is not None:
            user = User.objects.get(pk=user_id)
        if user.id is None:
            return super().get_queryset().none()
        if self.model.get_ct(self.model).model == "experiment":
            from .models import Experiment, ExperimentACL
            query = Experiment.objects.prefetch_related(Prefetch("experimentacl_set", queryset=ExperimentACL.objects.select_related("user"))
                                                ).filter(experimentacl__user=user,
                                                         experimentacl__isOwner=True,
                                                         ).exclude(experimentacl__effectiveDate__gte=datetime.today(),
                                                                   experimentacl__expiryDate__lte=datetime.today()
                                                                   )
        if self.model.get_ct(self.model).model == "dataset":
            from .models import Dataset, DatasetACL
            query = Dataset.objects.prefetch_related(Prefetch("datasetacl_set", queryset=DatasetACL.objects.select_related("user"))
                                                ).filter(datasetacl__user=user,
                                                         datasetacl__isOwner=True,
                                                         ).exclude(datasetacl__effectiveDate__gte=datetime.today(),
                                                                   datasetacl__expiryDate__lte=datetime.today()
                                                                   )
        if self.model.get_ct(self.model).model.replace(' ','') == "datafile":
            from .models import DataFile, DatafileACL
            query = DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("user"))
                                                ).filter(datafileacl__user=user,
                                                         datafileacl__isOwner=True,
                                                         ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                                   datafileacl__expiryDate__lte=datetime.today()
                                                                   )
        return query


    def _query_owned_by_group(self, group, group_id=None):
        if group_id is not None:
            group = Group.objects.get(pk=group_id)
        if group.id is None:
            return super().get_queryset().none()
        if self.model.get_ct(self.model).model == "experiment":
            from .models import Experiment, ExperimentACL
            query = Experiment.objects.prefetch_related(Prefetch("experimentacl_set", queryset=ExperimentACL.objects.select_related("group"))
                                                ).filter(experimentacl__group=group,
                                                         experimentacl__isOwner=True,
                                                         ).exclude(experimentacl__effectiveDate__gte=datetime.today(),
                                                                   experimentacl__expiryDate__lte=datetime.today()
                                                                   )
        if self.model.get_ct(self.model).model == "dataset":
            from .models import Dataset, DatasetACL
            query = Dataset.objects.prefetch_related(Prefetch("datasetacl_set", queryset=DatasetACL.objects.select_related("group"))
                                                ).filter(datasetacl__group=group,
                                                         datasetacl__isOwner=True,
                                                         ).exclude(datasetacl__effectiveDate__gte=datetime.today(),
                                                                   datasetacl__expiryDate__lte=datetime.today()
                                                                   )
        if self.model.get_ct(self.model).model.replace(' ','') == "datafile":
            from .models import DataFile, DatafileACL
            query = DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("group"))
                                                ).filter(datafileacl__group=group,
                                                         datafileacl__isOwner=True,
                                                         ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                                   datafileacl__expiryDate__lte=datetime.today()
                                                                   )
        return query


    def _query_shared(self, user):
        from .models.access_control import (ProjectACL, ExperimentACL,
                                            DatasetACL, DatafileACL)
        '''
        get all shared proj/exp/set/files, not owned ones
        '''
        # if the user is not authenticated, only tokens apply
        # this is almost duplicate code of end of has_perm in authorisation.py
        # should be refactored, but cannot think of good way atm
        if not user.is_authenticated:
            from .auth.token_auth import TokenGroupProvider

            if self.model.get_ct(self.model).model == "experiment":
                from .models import Experiment
                query = Experiment.objects.none()
            if self.model.get_ct(self.model).model == "dataset":
                from .models import Dataset
                query = Dataset.objects.none()
            if self.model.get_ct(self.model).model.replace(" ","") == "datafile":
                from .models import DataFile
                query = DataFile.objects.none()

            tgp = TokenGroupProvider()
            for token in tgp.getGroups(user):

                if self.model.get_ct(self.model).model == "experiment":
                    query |= Experiment.objects.prefetch_related(Prefetch("experimentacl_set", queryset=ExperimentACL.objects.select_related("token"))
                                                        ).filter(experimentacl__token=token,
                                                                 experimentacl__isOwner=False,
                                                                 ).exclude(experimentacl__effectiveDate__gte=datetime.today(),
                                                                           experimentacl__expiryDate__lte=datetime.today()
                                                                           )

                if self.model.get_ct(self.model).model == "dataset":
                    query |= Dataset.objects.prefetch_related(Prefetch("datasetacl_set", queryset=DatasetACL.objects.select_related("token"))
                                                        ).filter(datasetacl__token=token,
                                                                 datasetacl__isOwner=False,
                                                             ).exclude(datasetacl__effectiveDate__gte=datetime.today(),
                                                                           datasetacl__expiryDate__lte=datetime.today()
                                                                           )

                if self.model.get_ct(self.model).model.replace(' ','') == "datafile":
                    query |= DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("token"))
                                                        ).filter(datafileacl__token=token,
                                                                 datafileacl__isOwner=False,
                                                                 ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                                           datafileacl__expiryDate__lte=datetime.today()
                                                                           )
            return query
        # for which proj/exp/set/files does the user have read access
        # based on USER permissions?
        if self.model.get_ct(self.model).model == "experiment":
            from .models import Experiment
            query = Experiment.objects.prefetch_related(Prefetch("experimentacl_set", queryset=ExperimentACL.objects.select_related("user"))
                                                ).filter(experimentacl__user=user,
                                                         experimentacl__isOwner=False,
                                                         ).exclude(experimentacl__effectiveDate__gte=datetime.today(),
                                                                   experimentacl__expiryDate__lte=datetime.today()
                                                                   )

        if self.model.get_ct(self.model).model == "dataset":
            from .models import Dataset
            query = Dataset.objects.prefetch_related(Prefetch("datasetacl_set", queryset=DatasetACL.objects.select_related("user"))
                                                ).filter(datasetacl__user=user,
                                                         datasetacl__isOwner=False,
                                                         ).exclude(datasetacl__effectiveDate__gte=datetime.today(),
                                                                   datasetacl__expiryDate__lte=datetime.today()
                                                                   )

        if self.model.get_ct(self.model).model.replace(' ','') == "datafile":
            from .models import DataFile
            query = DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("user"))
                                                ).filter(datafileacl__user=user,
                                                         datafileacl__isOwner=False,
                                                         ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                                   datafileacl__expiryDate__lte=datetime.today()
                                                                   )
        # for which does proj/exp/set/files does the user have read access
        # based on GROUP permissions
            if self.model.get_ct(self.model).model == "experiment":
                from .models import Experiment
                query |= Experiment.objects.prefetch_related(Prefetch("experimentacl_set", queryset=ExperimentACL.objects.select_related("group"))
                                                    ).filter(experimentacl__group=group,
                                                             experimentacl__isOwner=False,
                                                             ).exclude(experimentacl__effectiveDate__gte=datetime.today(),
                                                                       experimentacl__expiryDate__lte=datetime.today()
                                                                       )

            if self.model.get_ct(self.model).model == "dataset":
                from .models import Dataset
                query |= Dataset.objects.prefetch_related(Prefetch("datasetacl_set", queryset=DatasetACL.objects.select_related("group"))
                                                    ).filter(datasetacl__group=group,
                                                             datasetacl__isOwner=False,
                                                             ).exclude(datasetacl__effectiveDate__gte=datetime.today(),
                                                                       datasetacl__expiryDate__lte=datetime.today()
                                                                       )

            if self.model.get_ct(self.model).model.replace(' ','') == "datafile":
                from .models import DataFile
                query |= DataFile.objects.prefetch_related(Prefetch("datafileacl_set", queryset=DatafileACL.objects.select_related("group"))
                                                    ).filter(datafileacl__group=group,
                                                             datafileacl__isOwner=False,
                                                             ).exclude(datafileacl__effectiveDate__gte=datetime.today(),
                                                                       datafileacl__expiryDate__lte=datetime.today()
                                                                       )
        return query


    def _query_owned_and_shared(self, user):
        return self._query_shared(user) | self._query_owned(user)


    def _query_all_public(self):
        from .models import Experiment
        return ~Q(public_access=Experiment.PUBLIC_ACCESS_NONE) &\
               ~Q(public_access=Experiment.PUBLIC_ACCESS_EMBARGO)


    def owned_by_user(self, user):
        """
        Return all experiments which are owned by a particular user id

        :param User user: a User Object
        :return: QuerySet of Experiments owned by user
        :rtype: QuerySet
        """
        query = self._query_owned(user)
        return super().get_queryset().filter(query)

    def owned_by_group(self, group):
        """
        Return all experiments that are owned by a particular group
        """
        query = self._query_owned_by_group(group)
        return super().get_queryset().filter(query)

    def owned_by_user_id(self, userId):
        """
        Return all experiments which are owned by a particular user id

        :param int userId: a User ID
        :returns: QuerySet of Experiments owned by user id
        :rtype: QuerySet
        """
        query = self._query_owned(user=None, user_id=userId)
        return super().get_queryset().filter(query)

    def user_acls(self, experiment_id):
        """
        Returns a list of ACL rules associated with this experiment.

        :param experiment_id: the ID of the experiment
        :type experiment_id: string
        :returns: QuerySet of ACLs
        :rtype: QuerySet
        """
        experiment = super().get(pk=experiment_id)

        return ObjectACL.objects.filter(
            pluginId=django_user,
            content_type=experiment.get_ct(),
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)

    def users(self, experiment_id):
        """
        Returns a list of users who have ACL rules associated with this
        experiment.

        :param int experiment_id: the ID of the experiment
        :returns: QuerySet of Users with experiment access
        :rtype: QuerySet
        """
        acl = self.user_acls(experiment_id)
        return User.objects.filter(pk__in=[int(a.entityId) for a in acl])

    def user_owned_groups(self, experiment_id):
        """
        returns a list of user owned-groups which have ACL rules
        associated with this experiment

        :param int experiment_id: the ID of the experiment to be edited
        :returns: QuerySet of non system Groups
        :rtype: QuerySet
        """

        acl = ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__model='experiment',
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)

        return Group.objects.filter(pk__in=[str(a.entityId) for a in acl])

    def group_acls_user_owned(self, experiment_id):
        """
        Returns a list of ACL rules associated with this experiment.

        :param int experiment_id: the ID of the experiment
        :returns: QuerySet of ACLs
        :rtype: QuerySet
        """
        return ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__model='experiment',
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.OWNER_OWNED)

    def group_acls_system_owned(self, experiment_id):
        """
        Returns a list of ACL rules associated with this experiment.

        :param int experiment_id: the ID of the experiment
        :returns: QuerySet of system-owned ACLs for experiment
        :rtype: QuerySet
        """
        return ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__model='experiment',
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.SYSTEM_OWNED)

    def system_owned_groups(self, experiment_id):
        """
        returns a list of sytem-owned groups which have ACL rules
        associated with this experiment

        :param experiment_id: the ID of the experiment to be edited
        :type experiment_id: string
        :returns: system owned groups for experiment
        :rtype: QuerySet
        """
        from .models import ObjectACL
        acl = ObjectACL.objects.filter(
            pluginId='django_group',
            content_type__model='experiment',
            object_id=experiment_id,
            aclOwnershipType=ObjectACL.SYSTEM_OWNED)

        return Group.objects.filter(pk__in=[str(a.entityId) for a in acl])

    def external_users(self, experiment_id):
        """
        returns a list of groups which have external ACL rules

        :param int experiment_id: the ID of the experiment to be edited
        :returns: list of groups with external ACLs
        :rtype: list
        """

        from .models import ObjectACL
        acl = ObjectACL.objects.exclude(pluginId=django_user)
        acl = acl.exclude(pluginId='django_group')
        acl = acl.filter(content_type__model='experiment',
                         object_id=experiment_id)

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
