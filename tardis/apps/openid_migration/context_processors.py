from django.urls import reverse
from tardis.tardis_portal.context_processors import user_menu_processor


def openid_migration_menu_processor(request):
    context = user_menu_processor(request)
    user_menu = context['user_menu']
    migrate_menu_item = dict(
        url=reverse('tardis.apps.openid_migration.views.migrate_accounts'),
        icon='fa fa-tags',
        label='Migrate Accounts'
    )
    item_index = -1
    for menu_item in user_menu:
        if menu_item.label == "Link Accounts":
            item_index = user_menu.index(menu_item)
    if item_index == -1:
        raise Exception("Couldn't find Link Accounts menu item to insert after.")
    user_menu.insert(item_index + 1, migrate_menu_item)
    return dict(user_menu=user_menu)
