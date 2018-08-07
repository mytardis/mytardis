from django.urls import reverse

from tardis.tardis_portal.context_processors import user_menu_processor


def sftp_menu_processor(request):
    if not request.user.has_perm('tardis_portal.change_userauthentication'):
        return dict()

    context = user_menu_processor(request)
    user_menu = context['user_menu']
    migrate_menu_item = dict(
        url=reverse('tardis.apps.sftp:sftp_keys'),
        icon='fa fa-key',
        label='Manage SSH Keys'
    )
    # Find the index of "Link Accounts" item so we can add item before this.
    # If we can't just add it above logout.
    item_index = next((i for i, menu_item in enumerate(user_menu)
                       if 'label' in menu_item
                       and menu_item['label'] == "Link Accounts"),
                      len(user_menu))

    user_menu.insert(item_index, migrate_menu_item)
    return dict(user_menu=user_menu)
