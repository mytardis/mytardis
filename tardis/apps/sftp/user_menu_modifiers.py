from django.urls import reverse


def add_ssh_keys_menu_item(request, user_menu):
    """Add a 'Manage SSH Keys' item to the user menu

    :param request: an HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param user_menu: user menu context to modify
    :type user_menu: list
    :return: user_menu list
    :rtype: list
    """
    ssh_keys_menu_item = dict(
        url=reverse('tardis.apps.sftp:sftp_keys'),
        icon='fa fa-key',
        label='Manage SSH Keys'
    )
    # Find the index of "Manage Account" item so we can add item after it.
    # If we can't find it, just insert it at the beginning
    item_index = next((i + 1 for i, menu_item in enumerate(user_menu)
                       if 'label' in menu_item
                       and menu_item['label'] == "Manage Account"),
                      0)

    user_menu.insert(item_index, ssh_keys_menu_item)
    return user_menu
