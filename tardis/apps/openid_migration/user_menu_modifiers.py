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
    if not request.user.has_perm('tardis_portal.change_userauthentication'):
        return user_menu

    migrate_menu_item = dict(
        url=reverse('tardis.apps.openid_migration.views.migrate_accounts'),
        icon='fa fa-tags',
        label='Migrate My Account'
    )
    item_index = -1
    for menu_item in user_menu:
        if 'label' in menu_item and menu_item['label'] == "Link Accounts":
            item_index = user_menu.index(menu_item)
            menu_item.update(migrate_menu_item)
    if item_index == -1:
        item_index = len(user_menu) - 1
        user_menu.insert(item_index, migrate_menu_item)
    return user_menu
