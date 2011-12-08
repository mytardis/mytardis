
from django.contrib import admin
from tardis.apps.hpctardis.models import PartyRecord
from tardis.apps.hpctardis.models import ActivityRecord
from tardis.apps.hpctardis.models import ActivityPartyRelation
from tardis.apps.hpctardis.models import ActivityLocation
from tardis.apps.hpctardis.models import PartyLocation

class ActivityPartyRelationInlines(admin.TabularInline):
    model = ActivityPartyRelation
    
    
    
class ActivityLocationInlines(admin.TabularInline):
    model = ActivityLocation
    extra = 1
    
    
class ActivityRecordAdmin(admin.ModelAdmin):
    inlines = (ActivityPartyRelationInlines,ActivityLocationInlines)


class PartyLocationInlines(admin.TabularInline):
    model = PartyLocation
    extra = 1
    
    
class PartyRecordAdmin(admin.ModelAdmin):
    inlines = (PartyLocationInlines,)
    
    
admin.site.register(PartyRecord,PartyRecordAdmin)
admin.site.register(ActivityRecord,ActivityRecordAdmin)
#admin.site.register(ActivityLocation)
#admin.site.register(PartyLocation)
