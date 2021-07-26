from django.contrib import admin
from tardis.apps.facility_profile.models import Institution, FacilityProfile

# Register PID models in admin site
admin.site.register(Institution)
admin.site.register(FacilityProfile)
