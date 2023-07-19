from django.conf import settings
from django.contrib import admin

from tardis.apps.identifiers.models import (
    DatasetID,
    ExperimentID,
    FacilityID,
    InstitutionID,
    InstrumentID,
    ProjectID,
)


# Register PID models in admin site
if "dataset" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(DatasetID)
if "experiment" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(ExperimentID)
if "facility" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(FacilityID)
if "instrument" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(InstrumentID)
if "institution" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(InstitutionID)

if (
    "tardis.apps.projects" in settings.INSTALLED_APPS
    and "project" in settings.OBJECTS_WITH_IDENTIFIERS
):
    admin.site.register(ProjectID)
