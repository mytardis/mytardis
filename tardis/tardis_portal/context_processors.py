from django.conf import settings
from tardis.tardis_portal.staging import get_full_staging_path


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


def manage_account_processor(request):
    return {'manage_account_enabled': getattr(
        settings, 'MANAGE_ACCOUNT_ENABLED', True)}


def user_details_processor(request):
    is_authenticated = request.user.is_authenticated
    if is_authenticated:
        is_superuser = request.user.is_superuser
        username = request.user.username
    else:
        is_superuser = False
        username = None
    staging = True if get_full_staging_path(username) else False
    return {'username': username,
            'is_authenticated': is_authenticated,
            'is_superuser': is_superuser,
            'has_staging_access': staging}


def global_contexts(request):
    site_title = getattr(settings, 'SITE_TITLE', None)
    sponsored_by = getattr(settings, 'SPONSORED_TEXT', None)
    site_styles = getattr(settings, 'SITE_STYLES', '')
    # Enables UI elements for the publication form:
    pub_form_enabled = ('tardis.apps.publication_forms'
                        in settings.INSTALLED_APPS)
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
