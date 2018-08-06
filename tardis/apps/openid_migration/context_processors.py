from django.conf import settings
from django.urls import reverse

from tardis.tardis_portal.context_processors import user_menu_processor


def openid_migration_processor(request):
    """
    adds context for openid_migration
    """
    def is_openid_migration_enabled():
        try:
            if 'tardis.apps.openid_migration' in settings.INSTALLED_APPS:
                return getattr(settings, 'OPENID_MIGRATION_ENABLED', True)
        except AttributeError:
            pass
        return False
    return {'openid_migration_enabled': is_openid_migration_enabled()}


def openid_migration_menu_processor(request):
    if not request.user.has_perm('tardis_portal.change_userauthentication'):
        return dict()

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
