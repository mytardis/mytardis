from django.conf import settings
from django.contrib import admin
from tardis.apps.identifiers.models import (DatasetPID, ExperimentPID,
                                            FacilityPID, InstrumentPID,
                                            ProjectPID)

# Register PID models in admin site
if "dataset" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(DatasetPID)
if "experiment" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(ExperimentPID)
if "facility" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(FacilityPID)
if "instrument" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(InstrumentPID)
if (
    "tardis.apps.projects" in settings.INSTALLED_APPS
    and "project" in settings.OBJECTS_WITH_IDENTIFIERS
):
    admin.site.register(ProjectPID)
