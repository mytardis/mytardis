from django.conf import settings


def openid_migration_processor(request):
    """
    adds context for openid_migration
    """

    def is_openid_migration_enabled():
        try:
            if "tardis.apps.openid_migration" in settings.INSTALLED_APPS:
                return getattr(settings, "OPENID_MIGRATION_ENABLED", True)
        except AttributeError:
            pass
        return False

    return {"openid_migration_enabled": is_openid_migration_enabled()}
