# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#


from django import forms
from django.forms import TextInput
import django.db
from django.contrib import admin

from . import models

# from south.models import MigrationHistory


class ExperimentParameterInline(admin.TabularInline):
    model = models.ExperimentParameter
    extra = 0
    formfield_overrides = {
        django.db.models.TextField: {'widget': TextInput},
    }


class ExperimentParameterSetAdmin(admin.ModelAdmin):
    inlines = [ExperimentParameterInline]


class InstrumentParameterInline(admin.TabularInline):
    model = models.InstrumentParameter
    extra = 0


class InstrumentParameterSetAdmin(admin.ModelAdmin):
    inlines = [InstrumentParameterInline]


class ExperimentACLInline(admin.TabularInline):
    model = models.ExperimentACL
    extra = 0

class DatasetACLInline(admin.TabularInline):
    model = models.DatasetACL
    extra = 0

class DatafileACLInline(admin.TabularInline):
    model = models.DatafileACL
    extra = 0


class ExperimentAdmin(admin.ModelAdmin):
    search_fields = ['title', 'id']
    inlines = [ExperimentACLInline]


class DatasetAdmin(admin.ModelAdmin):
    search_fields = ['description', 'id']


class StorageBoxAttributeInlineForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = models.StorageBoxAttribute
        widgets = {
            'key': TextInput(attrs={'size': 40}),
            'value': TextInput(attrs={'size': 80})
        }


class StorageBoxAttributeInline(admin.TabularInline):
    model = models.StorageBoxAttribute
    extra = 0
    form = StorageBoxAttributeInlineForm


class StorageBoxOptionInlineForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = models.StorageBoxOption
        widgets = {
            'key': TextInput(attrs={'size': 40}),
            'value': TextInput(attrs={'size': 80})
        }


class StorageBoxOptionInline(admin.TabularInline):
    model = models.StorageBoxOption
    extra = 0
    form = StorageBoxOptionInlineForm


class StorageBoxForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = models.StorageBox
        widgets = {
            'django_storage_class': TextInput(attrs={'size': 120}),
            'name': TextInput(attrs={'size': 120}),
            'description': TextInput(attrs={'size': 120}),
        }


class StorageBoxAdmin(admin.ModelAdmin):
    search_fields = ['name']
    inlines = [StorageBoxOptionInline,
               StorageBoxAttributeInline]
    form = StorageBoxForm


class DataFileObjectInlineForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = models.DataFileObject
        widgets = {
            'uri': TextInput(attrs={'size': 120}),
        }


class DataFileObjectInline(admin.TabularInline):
    model = models.DataFileObject
    extra = 0
    form = DataFileObjectInlineForm


class DatafileAdminForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = models.DataFile
        widgets = {
            'directory': TextInput(attrs={'size': 120}),
        }


class DatafileAdmin(admin.ModelAdmin):
    search_fields = ['filename', 'id']
    form = DatafileAdminForm
    inlines = [DataFileObjectInline, ]


class ParameterNameInline(admin.TabularInline):
    model = models.ParameterName
    extra = 0


class SchemaAdmin(admin.ModelAdmin):
    search_fields = ['name', 'namespace']
    inlines = [ParameterNameInline]


class ParameterNameAdmin(admin.ModelAdmin):
    search_fields = ['name', 'schema__id']


class ExperimentACLAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'pluginId', 'entityId', 'canRead',
        'canWrite', 'canDelete', 'isOwner'
    ]

class DatasetACLAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'pluginId', 'entityId', 'canRead',
        'canWrite', 'canDelete', 'isOwner'
    ]

class DatafileACLAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'pluginId', 'entityId', 'canRead',
        'canWrite', 'canDelete', 'isOwner'
    ]


class FreeTextSearchFieldAdmin(admin.ModelAdmin):
    pass


class UserAuthenticationAdmin(admin.ModelAdmin):
    search_fields = [
        'username',
        'authenticationMethod',
        'userProfile__user__username'
        ]


class FacilityAdmin(admin.ModelAdmin):
    search_fields = ['name']


class InstrumentAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(models.Facility, FacilityAdmin)
admin.site.register(models.Instrument, InstrumentAdmin)
admin.site.register(models.Experiment, ExperimentAdmin)
admin.site.register(models.License)
admin.site.register(models.Dataset, DatasetAdmin)
admin.site.register(models.DataFile, DatafileAdmin)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.ParameterName, ParameterNameAdmin)
admin.site.register(models.DatafileParameter)
admin.site.register(models.DatasetParameter)
admin.site.register(models.InstrumentParameter)
admin.site.register(models.ExperimentAuthor)
admin.site.register(models.UserProfile)
admin.site.register(models.ExperimentParameter)
admin.site.register(models.DatafileParameterSet)
admin.site.register(models.DatasetParameterSet)
admin.site.register(models.InstrumentParameterSet, InstrumentParameterSetAdmin)
admin.site.register(models.Token)
admin.site.register(models.ExperimentParameterSet, ExperimentParameterSetAdmin)
admin.site.register(models.GroupAdmin)
admin.site.register(models.UserAuthentication, UserAuthenticationAdmin)
admin.site.register(models.ExperimentACL, ExperimentACLAdmin)
admin.site.register(models.DatasetACL, DatasetACLAdmin)
admin.site.register(models.DatafileACL, DatafileACLAdmin)
admin.site.register(models.FreeTextSearchField, FreeTextSearchFieldAdmin)
# admin.site.register(MigrationHistory)
admin.site.register(models.StorageBox, StorageBoxAdmin)
admin.site.register(models.StorageBoxOption)
admin.site.register(models.StorageBoxAttribute)
admin.site.register(models.DataFileObject)
