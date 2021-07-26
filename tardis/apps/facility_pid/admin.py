from django.contrib import admin
from tardis.apps.facility_pid.models import FacilityPID  # noqa

# Register PID models in admin site
admin.site.register(FacilityPID)
