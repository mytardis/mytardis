from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r"^migrate-accounts/$",
        views.migrate_accounts,
        name="tardis.apps.openid_migration.views.migrate_accounts",
    ),
]
