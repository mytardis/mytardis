
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

class ActivityPartyRelationInlines(admin.TabularInline):
    model = ActivityPartyRelation
    
    
    
class ActivityLocationInlines(admin.TabularInline):
    model = ActivityLocation
    extra = 1
    
    
class ActivityDescriptionInlines(admin.TabularInline):
    model = ActivityDescription
    extra = 1
    
    
class ActivityRecordAdmin(admin.ModelAdmin):
    inlines = (ActivityPartyRelationInlines,ActivityLocationInlines, ActivityDescriptionInlines)


class PartyLocationInlines(admin.TabularInline):
    model = PartyLocation
    extra = 1
    
    
class PartyDescriptionInlines(admin.TabularInline):
    model = PartyDescription
    extra = 1
    
    
class PartyRecordAdmin(admin.ModelAdmin):
    inlines = (PartyLocationInlines,PartyDescriptionInlines)
    
    
admin.site.register(NameParts)
#admin.site.register(PartyDescription)
#admin.site.register(ActivityDescription)
admin.site.register(PublishAuthorisation)
admin.site.register(PartyRecord,PartyRecordAdmin)
admin.site.register(ActivityRecord,ActivityRecordAdmin)
#admin.site.register(ActivityLocation)
#admin.site.register(PartyLocation)
