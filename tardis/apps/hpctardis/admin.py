# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, RMIT e-Research Office
#   (RMIT University, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of RMIT University nor the
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
from tardis.apps.hpctardis.models import PartyRecord
from tardis.apps.hpctardis.models import ActivityRecord
from tardis.apps.hpctardis.models import ActivityPartyRelation
from tardis.apps.hpctardis.models import ActivityLocation
from tardis.apps.hpctardis.models import PartyLocation
from tardis.apps.hpctardis.models import NameParts
from tardis.apps.hpctardis.models import PartyDescription
from tardis.apps.hpctardis.models import ActivityDescription
from tardis.apps.hpctardis.models import PublishAuthorisation

class ActivityPartyRelationInlines(admin.StackedInline):
    model = ActivityPartyRelation
    
    
    
class ActivityLocationInlines(admin.StackedInline):
    model = ActivityLocation
    extra = 0
    
    
class ActivityDescriptionInlines(admin.StackedInline):
    model = ActivityDescription
    extra = 0



#from django import forms

#class ProductAdminForm(forms.ModelForm):
#    choices = (("yes",'y'),('no','n'))
    
#    def __init__(self, *args, **kwargs):
#        super(ProductAdminForm, self).__init__(*args, **kwargs)
#        self.fields['type'].widget = forms.Select(self.choices)
            
    
class ActivityRecordAdmin(admin.ModelAdmin):
    inlines = (ActivityPartyRelationInlines, ActivityDescriptionInlines)
    #filter_horizontal = ('parties',)
    list_display = ('activityname','type','key',)
    ordering = ('id',)
    list_filter = ('type','key','parties')
    search_fields = ('activityname__title',
                     'activityname__given',
                     'activityname__family','activityname__suffix',)
    exclude = ('description',)
    
    #form = ProductAdminForm
    

class PartyLocationInlines(admin.StackedInline):
    model = PartyLocation
    extra = 0
    
    
class PartyDescriptionInlines(admin.StackedInline):
    model = PartyDescription
    extra = 0
    
    
class PartyRecordAdmin(admin.ModelAdmin):
    inlines = (PartyLocationInlines,PartyDescriptionInlines)
    list_display = ('partyname','type','key')
    #list_filter = ('publication_date',)
    #date_hierarchy = 'publication_date'
    ordering = ('id',)
    list_filter = ('type','key')
    search_fields = ('partyname__title','partyname__given','partyname__family','partyname__suffix',)
    
    
    
admin.site.register(NameParts)
#admin.site.register(PartyDescription)
#admin.site.register(ActivityDescription)
admin.site.register(PublishAuthorisation)
admin.site.register(PartyRecord,PartyRecordAdmin)
admin.site.register(ActivityRecord,ActivityRecordAdmin)
#admin.site.register(ActivityLocation)
#admin.site.register(PartyLocation)
