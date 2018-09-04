from django.urls import reverse


def add_migrate_account_menu_item(request, user_menu):
    """Add a 'Migrate My Account' item to the user menu

    :param request: an HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param user_menu: user menu context to modify
    :type user_menu: list
    :return: user_menu list
    :rtype: list
    """
    if not request.user.has_perm('openid_migration.add_openidusermigration'):
        return user_menu

    migrate_menu_item = dict(
        url=reverse('tardis.apps.openid_migration.views.migrate_accounts'),
        icon='fa fa-user',
        label='Migrate My Account'
    )
    user_menu.insert(0, migrate_menu_item)
    return user_menu
