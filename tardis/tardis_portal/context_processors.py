from django.conf import settings
from django.urls import reverse


def single_search_processor(request):

    context = {}
    single_search_on = False
    try:
        if settings.SINGLE_SEARCH_ENABLED:
            single_search_on = True
    except AttributeError:
        pass

    context = {
        'search_form': single_search_on,
    }

    return context


def registration_processor(request):
    def is_registration_enabled():
        try:
            if 'registration' in settings.INSTALLED_APPS:
                return getattr(settings, 'REGISTRATION_OPEN', True)
        except AttributeError:
            pass
        return False
    return {'registration_enabled': is_registration_enabled()}


def user_details_processor(request):
    is_authenticated = request.user.is_authenticated
    if is_authenticated:
        is_superuser = request.user.is_superuser
        username = request.user.username
    else:
        is_superuser = False
        username = None
    return {'username': username,
            'is_authenticated': is_authenticated,
            'is_superuser': is_superuser}


def global_contexts(request):
    site_title = getattr(settings, 'SITE_TITLE', None)
    sponsored_by = getattr(settings, 'SPONSORED_TEXT', None)
    site_styles = getattr(settings, 'SITE_STYLES', '')
    version = getattr(settings, 'MYTARDIS_VERSION', None)
    return {'site_title': site_title,
            'sponsored_by': sponsored_by,
            'site_styles': site_styles,
            'version': version, }


def google_analytics(request):
    """
    adds context for portal_template.html
    """
    ga_id = getattr(settings, 'GOOGLE_ANALYTICS_ID', '')
    ga_host = getattr(settings, 'GOOGLE_ANALYTICS_HOST', 'auto')
    ga_enabled = ga_id != '' and ga_host != ''
    return {'ga_enabled': ga_enabled,
            'ga_id': ga_id,
            'ga_host': ga_host}


def user_menu_processor(request):
    manage_account_enabled = getattr(settings, 'MANAGE_ACCOUNT_ENABLED', True)
    user_menu = []
    if not request.user.is_authenticated:
        return dict(user_menu=user_menu)
    if manage_account_enabled:
        user_menu.append(dict(
            url=reverse('tardis.tardis_portal.views.manage_user_account'),
            icon='fa fa-user',
            label='Manage Account'))
    if hasattr(request.user, 'api_key') and request.user.api_key.key:
        user_menu.append(dict(
            url=reverse('tardis.tardis_portal.download.download_api_key'),
            icon='fa fa-key',
            label='Download Api Key'))
    if request.user.has_perm('tardis_portal.change_userauthentication'):
        user_menu.append(dict(
            url=reverse('tardis.tardis_portal.views.manage_auth_methods'),
            icon='fa fa-tags',
            label='Link Accounts'))
    if request.user.is_superuser:
        user_menu.append(dict(
            url=reverse('admin:index'),
            icon='fa fa-key',
            label='Admin Interface'))
    if request.user.has_perm('auth.change_user') or \
            request.user.has_perm('auth.change_group'):
        user_menu.append(dict(divider='True'))
        user_menu.append(dict(
            url=reverse('tardis.tardis_portal.views.manage_groups'),
            icon='fa fa-user',
            style='text-shadow: 2px -2px #666666',
            label='Group Management'))
        user_menu.append(dict(divider='True'))
    user_menu.append(dict(
        url=reverse('django.contrib.auth.views.logout'),
        icon='fa fa-signout',
        label='Log Out'))
    return dict(user_menu=user_menu)
