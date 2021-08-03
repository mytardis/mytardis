from django.contrib import admin
from tardis.apps.facilityprofile.models import FacilityProfile

# Register PID models in admin site
admin.site.register(FacilityProfile)
