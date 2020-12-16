from django.contrib import admin

from .models import Log


class LogAdmin(admin.ModelAdmin):
    raw_id_fields = ["user"]
    list_filter = ["action__name", "timestamp"]
    list_display = ["timestamp", "user", "action", "extra"]
    search_fields = ["user__username", "user__email", "extra"]


admin.site.register(Log, LogAdmin)
