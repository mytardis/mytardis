from django.conf import settings
from django.contrib import admin

from tardis.apps.dataclassification import (
    DatasetDataClassification,
    ExperimentDataClassification,
    ProjectDataClassification,
)

admin.site.register(DatasetDataClassification)
admin.site.register(ExperimentDataClassification)

admin.site.register(ProjectDataClassification)
