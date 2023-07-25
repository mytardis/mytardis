from django.conf import settings
from django.contrib import admin

from tardis.apps.autoarchive.models import (
    DataFileAutoArchive,
    ExperimentAutoArchive,
    ProjectAutoArchive,
)

admin.site.register(DataFileAutoArchive)
if "tardis.apps.projects" in settings.INSTALLED_APPS:
    admin.site.register(ProjectAutoArchive)
admin.site.register(ExperimentAutoArchive)
