from django.cong import settings
from django.contrib import admin
from tardis.apps.identifiers.models import (
    DatasetPID,
    ExperimentPID,
    FacilityPID,
    InstrumentPID,
)

# Register PID models in admin site
if "dataset" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(DatasetPID)
if "experiment" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(ExperimentPID)
if "facility" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(FacilityPID)
if "instrument" in settings.OBJECTS_WITH_IDENTIFIERS:
    admin.site.register(InstrumentPID)
