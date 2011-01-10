from django.db import models
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group

from datetime import datetime


class ExperimentManager(models.Manager):

    def all(self, request):
        query = Q(public=True)

        if request.user.is_authenticated():
            query |= Q(experimentacl__pluginId='user',
                       experimentacl__entityId=str(request.user.id),
                       experimentacl__isOwner=True)

            query |= Q(experimentacl__pluginId='user',
                       experimentacl__entityId=str(request.user.id),
                       experimentacl__canRead=True)\
                       & (Q(experimentacl__effectiveDate__lte=datetime.today())
                          | Q(experimentacl__effectiveDate__isnull=True))\
                       & (Q(experimentacl__expiryDate__gte=datetime.today())
                          | Q(experimentacl__expiryDate__isnull=True))

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
        experiment = \
            super(ExperimentManager, self).get(pk=experiment_id)

        if experiment.public:
            return experiment

        if not request.user.is_authenticated():
            raise PermissionDenied

        query = Q(experiment=experiment,
                  pluginId='user',
                  entityId=str(request.user.id),
                  isOwner=True)

        query |= Q(experiment=experiment,
                   pluginId='user',
                   entityId=str(request.user.id),
                   canRead=True)\
                   & (Q(effectiveDate__lte=datetime.today())
                      | Q(effectiveDate__isnull=True))\
                   & (Q(expiryDate__gte=datetime.today())
                      | Q(expiryDate__isnull=True))

        for name, group in request.groups:
            query |= Q(pluginId=name,
                       entityId=str(group),
                       experiment=experiment,
                       canRead=True)\
                       & (Q(effectiveDate__lte=datetime.today())
                          | Q(effectiveDate__isnull=True))\
                       & (Q(expiryDate__gte=datetime.today())
                          | Q(expiryDate__isnull=True))

        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.filter(query)
        if acl.count() == 0:
            raise PermissionDenied
        else:
            return experiment

    def owned(self, request):
        if not request.user.is_authenticated():
            return []

        from tardis.tardis_portal.models import ExperimentACL
        experiments = super(ExperimentManager, self).get_query_set().filter(
            experimentacl__pluginId='user',
            experimentacl__entityId=str(request.user.id),
            experimentacl__isOwner=True,
            experimentacl__aclOwnershipType=ExperimentACL.OWNER_OWNED
            )

        return experiments

    def users(self, request, experiment_id):
        # TODO: Lookup ALL users through UserProvider
        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.filter(pluginId='user',
                                           experiment__id=experiment_id,
                                           aclOwnershipType=ExperimentACL.OWNER_OWNED)

        return [User.objects.get(pk=str(a.entityId)) for a in acl]

    def groups(self, request, experiment_id):
        from tardis.tardis_portal.models import ExperimentACL
        acl = ExperimentACL.objects.filter(pluginId='django_groups',
                                           experiment__id=experiment_id,
                                           aclOwnershipType=ExperimentACL.OWNER_OWNED)

        return [Group.objects.get(pk=str(a.entityId)) for a in acl]
