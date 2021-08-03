from django.contrib import admin
from tardis.apps.instrumentpid.models import InstrumentPID  # noqa

# Register PID models in admin site
admin.site.register(InstrumentPID)
