from django.contrib import admin
from .models import DatasetPID  # noqa

# Register PID models in admin site
admin.site.register(DatasetPID)
