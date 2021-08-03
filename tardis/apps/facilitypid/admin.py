from django.contrib import admin
from tardis.apps.facilitypid.models import FacilityPID  # noqa

# Register PID models in admin site
admin.site.register(FacilityPID)
