from importlib import import_module

from django.conf import settings
from django.urls import reverse

from tardis.tardis_portal.templatetags.approved_user_tags import (
    check_if_user_not_approved,
)


def single_search_processor(request):
    context = {}
    single_search_on = False
    try:
        if settings.SINGLE_SEARCH_ENABLED:
            single_search_on = True
    except AttributeError:
        pass

    context = {
        "search_form": single_search_on,
    }

    return context


def project_app_processor(request):
    return {"project_app_enabled": "tardis.apps.projects" in settings.INSTALLED_APPS}


def disable_creation_forms_processor(request):
    return {"disable_creation_forms": settings.DISABLE_CREATION_FORMS}


def registration_processor(request):
    def is_registration_enabled():
        try:
            if "registration" in settings.INSTALLED_APPS:
                return getattr(settings, "REGISTRATION_OPEN", True)
        except AttributeError:
            pass
        return False

    return {"registration_enabled": is_registration_enabled()}


def user_details_processor(request):
    is_authenticated = request.user.is_authenticated
    if is_authenticated:
        is_superuser = request.user.is_superuser
        username = request.user.username
    else:
        is_superuser = False
        username = None
    return {
        "username": username,
        "is_authenticated": is_authenticated,
        "is_superuser": is_superuser,
    }


def global_contexts(request):
    site_title = getattr(settings, "SITE_TITLE", None)
    sponsored_by = getattr(settings, "SPONSORED_TEXT", None)
    site_styles = getattr(settings, "SITE_STYLES", "")
    version = getattr(settings, "MYTARDIS_VERSION", None)
    return {
        "site_title": site_title,
        "sponsored_by": sponsored_by,
        "site_styles": site_styles,
        "version": version,
    }


def google_analytics(request):
    """
    adds context for portal_template.html
    """
    ga_id = getattr(settings, "GOOGLE_ANALYTICS_ID", "")
    ga_host = getattr(settings, "GOOGLE_ANALYTICS_HOST", "auto")
    ga_enabled = ga_id != "" and ga_host != ""
    return {"ga_enabled": ga_enabled, "ga_id": ga_id, "ga_host": ga_host}


def user_menu_processor(request):
    manage_account_enabled = getattr(settings, "MANAGE_ACCOUNT_ENABLED", True)
    link_accounts_enabled = getattr(settings, "LINK_ACCOUNTS_ENABLED", True)
    user_menu = []
    if not request.user.is_authenticated:
        return {"user_menu": user_menu}
    if manage_account_enabled:
        user_menu.append(
            {
                "url": reverse("tardis.tardis_portal.views.manage_user_account"),
                "icon": "fa fa-user",
                "label": "Manage Account",
            }
        )
    if (
        hasattr(request.user, "api_key")
        and request.user.api_key.key
        and not check_if_user_not_approved(request)
    ):
        user_menu.append(
            {
                "url": reverse("tardis.tardis_portal.download.download_api_key"),
                "icon": "fa fa-key",
                "label": "Download Api Key",
            }
        )
    if link_accounts_enabled and request.user.has_perm(
        "tardis_portal.change_userauthentication"
    ):
        user_menu.append(
            {
                "url": reverse("tardis.tardis_portal.views.manage_auth_methods"),
                "icon": "fa fa-tags",
                "label": "Link Accounts",
            }
        )
    if request.user.is_superuser:
        user_menu.append(
            {
                "url": reverse("admin:index"),
                "icon": "fa fa-key",
                "label": "Admin Interface",
            }
        )
    if (
        request.user.has_perm("auth.change_user")
        or request.user.has_perm("auth.change_group")
    ) and not check_if_user_not_approved(request):
        user_menu.append({"divider": "True"})
        user_menu.append(
            {
                "url": reverse("tardis.tardis_portal.views.manage_groups"),
                "icon": "fa fa-user",
                "style": "text-shadow: 2px -2px #666666",
                "label": "Group Management",
            }
        )
        user_menu.append({"divider": "True"})
    user_menu.append(
        {"url": reverse("logout"), "icon": "fa fa-sign-out", "label": "Log Out"}
    )

    user_menu_modifiers = getattr(settings, "USER_MENU_MODIFIERS", [])
    for user_menu_modifier in user_menu_modifiers:
        module_path, method_name = user_menu_modifier.rsplit(".", 1)
        module = import_module(module_path)
        method = getattr(module, method_name)
        user_menu = method(request, user_menu)
    return {"user_menu": user_menu}
