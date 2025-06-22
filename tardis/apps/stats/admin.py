from django.contrib import admin

from .models import UserStat


class UserStatAdmin(admin.ModelAdmin):
    raw_id_fields = ["user"]
    list_filter = ["stat__name", "date"]
    list_display = ["date", "user", "stat", "str_value", "int_value",
                    "bigint_value", "datetime_value"]
    search_fields = ["user__username", "user__email", "stat_name"]


admin.site.register(UserStat, UserStatAdmin)
