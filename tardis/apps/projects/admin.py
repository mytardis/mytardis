from django import forms
from django.forms import TextInput
import django.db
from django.contrib import admin

from . import models


class ProjectParameterInline(admin.TabularInline):
    model = models.ProjectParameter
    extra = 0
    formfield_overrides = {
        django.db.models.TextField: {"widget": TextInput},
    }


class ProjectParameterSetAdmin(admin.ModelAdmin):
    inlines = [ProjectParameterInline]


class ProjectACLInline(admin.TabularInline):
    model = models.ProjectACL
    extra = 0


class ProjectAdmin(admin.ModelAdmin):
    search_fields = ["name", "id"]
    inlines = [ProjectACLInline]


class ProjectACLAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "canRead",
        "canDownload",
        "canWrite",
        "canDelete",
        "canSensitive",
        "isOwner",
    ]


admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.ProjectParameterSet, ProjectParameterSetAdmin)
admin.site.register(models.ProjectParameter)
admin.site.register(models.ProjectACL, ProjectACLAdmin)
admin.site.register(models.DefaultInstitutionProfile)
