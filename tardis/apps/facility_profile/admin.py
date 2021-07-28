from django.contrib import admin
from tardis.apps.facility_profile.models import FacilityProfile

# Register PID models in admin site
admin.site.register(FacilityProfile)
