from django.urls import reverse

from tardis.apps.openid_migration.models import OpenidUserMigration


def add_migrate_account_menu_item(request, user_menu):
    """Add a 'Migrate My Account' item to the user menu

    :param request: an HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param user_menu: user menu context to modify
    :type user_menu: list
    :return: user_menu list
    :rtype: list
    """
    # check if account is migrated
    is_account_migrated = OpenidUserMigration.objects.filter(new_user=request.user)
    if (
        not request.user.has_perm("openid_migration.add_openidusermigration")
        or is_account_migrated
    ):
        return user_menu

    migrate_menu_item = {
        "url": reverse("tardis.apps.openid_migration.views.migrate_accounts"),
        "icon": "fa fa-user",
        "label": "Migrate My Account",
    }
    user_menu.insert(0, migrate_menu_item)
    return user_menu
