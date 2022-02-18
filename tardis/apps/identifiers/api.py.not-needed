"""
RESTful API for persistent identifier apps.
Implemented with TastyPie.

 .. moduleauthor:: Chris Seal <c.seal@auckland.ac.nz>
"""

from django.conf import settings
from tardis.apps.identifiers.models import (DatasetPID, ExperimentPID,
                                            FacilityPID, InstrumentPID,
                                            ProjectPID)
from tardis.apps.projects.api import ProjectACLAuthorization, ProjectResource
from tardis.tardis_portal.api import (ACLAuthorization, DatasetResource,
                                      ExperimentResource, FacilityResource,
                                      InstrumentResource,
                                      MyTardisAuthentication,
                                      PrettyJSONSerializer)
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer

if settings.DEBUG:
    default_serializer = PrettyJSONSerializer()
else:
    default_serializer = Serializer()


class DatasetPIDResource(ModelResource):
    """API for Dataset identifiers"""

    dataset = fields.OneToOneField(DatasetResource, "dataset")

    class Meta:
        authentication = MyTardisAuthentication()
        authorization = ACLAuthorization()
        serializer = default_serializer
        object_class = DatasetPID
        queryset = DatasetPID.objects.all()
        filtering = {
            "id": ("exact"),
            "dataset": ALL_WITH_RELATIONS,
            "persistent_id": ("exact"),
            "alternate_ids": ("contains"),
        }
        ordering = ["id", "dataset", "persistent_id", "alternate_ids"]
        always_return_data = True
