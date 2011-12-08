
from django.contrib import admin
from tardis.apps.hpctardis.models import PartyRecord
from tardis.apps.hpctardis.models import ActivityRecord
from tardis.apps.hpctardis.models import ActivityPartyRelation

class ActivityPartyRelationInlines(admin.TabularInline):
    model = ActivityPartyRelation
    
class ActivityRecordAdmin(admin.ModelAdmin):
    inlines = (ActivityPartyRelationInlines,)

admin.site.register(PartyRecord)
admin.site.register(ActivityRecord,ActivityRecordAdmin)
