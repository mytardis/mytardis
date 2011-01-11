from django.db import models
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group

from datetime import datetime


class ExperimentManager(models.Manager):
    """
    Implements a custom manager for the Experiment model which checks
    the authorisation rules for the requesting user first

    To make this work, the request must be passed to all class
    functions. The username and the group memberships are then
    resolved via the request.groups and request.user objects.

    The :py:tardis.tardis_portal.auth.AuthService: is responsible for
    filling the request.groups object.

    """
    def all(self, request):
        """
        Returns all experiments a user - either authenticated or
        anonymous - is allowed to see and search
        """

        # experiment is public?
        query = Q(public=True)

        # if the user is not authenticated, they will see only public
        # experiments
        if request.user.is_authenticated():
            # which experiments are owned by the user?
            query |= Q(experimentacl__pluginId='user',
                       experimentacl__entityId=str(request.user.id),
                       experimentacl__isOwner=True)

            # for which experiments does the user have read access
            # based on USER permissions?
            query |= Q(experimentacl__pluginId='user',
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

        return super(ExperimentManager, self).get_query_set().filter(query)

    def get(self, request, experiment_id):
        """
        Returns an experiment under the consideration of the ACL rules
        Raises PermissionDenied if the user does not have access.
        """
        experiment = \
            super(ExperimentManager, self).get(pk=experiment_id)

        # if the experiment is public, return it right away
        if experiment.public:
            return experiment

        # if not, is the user logged in at all?
        if not request.user.is_authenticated():
            raise PermissionDenied

        # does the user own this experiment?
        query = Q(experiment=experiment,
                  pluginId='user',
                  entityId=str(request.user.id),
                  isOwner=True)

        # check if there is a user based authorisation role
        query |= Q(experiment=experiment,
                   pluginId='user',
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
        """

        # the user must be authenticated
        if not request.user.is_authenticated():
            return []

        # build the query to filter the ACL table
        from tardis.tardis_portal.models import ExperimentACL
        experiments = super(ExperimentManager, self).get_query_set().filter(
            experimentacl__pluginId='user',
            experimentacl__entityId=str(request.user.id),
            experimentacl__isOwner=True,
            experimentacl__aclOwnershipType=ExperimentACL.OWNER_OWNED
            )

        return experiments

    def users(self, request, experiment_id):
        """
        returns a list of users which have ACL rules associated with
        this to this experiment
        """

        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.filter(experiment__id=experiment_id,
                                           aclOwnershipType=ExperimentACL.OWNER_OWNED)
        plugins = {}
        for a in acl:
            if not a.pluginId in plugins.keys():
                plugins[a.pluginId] = [a.entityId]
            else:
                plugins[a.pluginId] += [a.entityId]

        # TODO: Lookup ALL users through different UserProviders
        return [User.objects.get(pk=int(u)) for u in plugins['user']]

    def groups(self, request, experiment_id):
        """
        returns a list of groups which have ACL rules associated with
        this to this experiment
        """

        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.filter(pluginId='django_groups',
                                           experiment__id=experiment_id,
                                           aclOwnershipType=ExperimentACL.OWNER_OWNED)

        return [Group.objects.get(pk=str(a.entityId)) for a in acl]
