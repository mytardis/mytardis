from django.contrib import admin
from tardis.apps.institution.models import Institution

# Register PID models in admin site
admin.site.register(Institution)
