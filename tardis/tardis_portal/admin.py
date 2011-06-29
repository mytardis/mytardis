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


from django.contrib import admin
from tardis.tardis_portal import models
# from south.models import MigrationHistory

class ExperimentAdmin(admin.ModelAdmin):
    search_fields = ['title', 'id']


class DatasetAdmin(admin.ModelAdmin):
    search_fields = ['description', 'experiment__id']


class DatafileAdmin(admin.ModelAdmin):
    search_fields = ['filename', 'dataset__experiment__id']


class SchemaAdmin(admin.ModelAdmin):
    search_fields = ['name', 'namespace']


class ParameterNameAdmin(admin.ModelAdmin):
    search_fields = ['name', 'schema__id']


class ExperimentAclAdmin(admin.ModelAdmin):
    search_fields = ['experiment__id']



admin.site.register(models.Experiment, ExperimentAdmin)
admin.site.register(models.Dataset, DatasetAdmin)
admin.site.register(models.Dataset_File, DatafileAdmin)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.ParameterName, ParameterNameAdmin)
admin.site.register(models.DatafileParameter)
admin.site.register(models.DatasetParameter)
admin.site.register(models.Author_Experiment)
admin.site.register(models.UserProfile)
admin.site.register(models.ExperimentParameter)
admin.site.register(models.DatafileParameterSet)
admin.site.register(models.DatasetParameterSet)
admin.site.register(models.ExperimentParameterSet)
admin.site.register(models.GroupAdmin)
admin.site.register(models.UserAuthentication)
admin.site.register(models.ExperimentACL, ExperimentAclAdmin)
# admin.site.register(MigrationHistory)
