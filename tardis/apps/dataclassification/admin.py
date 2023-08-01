from django.conf import settings
from django.contrib import admin

from tardis.apps.dataclassification import (
    DatasetDataClassification,
    ExperimentDataClassification,
    ProjectDataClassification,
)

admin.site.register(DatasetDataClassification)
admin.site.register(ExperimentDataClassification)
if "tardis.apps.projects" in settings.INSTALLED_APPS:
    admin.site.register(ProjectDataClassification)
