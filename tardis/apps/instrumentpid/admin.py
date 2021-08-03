from django.contrib import admin
from tardis.apps.instrument_pid.models import InstrumentPID  # noqa

# Register PID models in admin site
admin.site.register(InstrumentPID)
