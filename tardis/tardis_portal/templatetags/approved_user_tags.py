from django import template
from django.conf import settings

from tardis.tardis_portal.models import UserAuthentication

register = template.Library()


@register.filter
def check_if_user_not_approved(request):
    """
    Custom template filter to identify whether a user account
    is approved.
    """
    if request.user.is_authenticated:
        user = request.user
        if not hasattr(request, "session"):
            # This should only happen in unit tests
            return False
        # get authenticated user backend
        backend = request.session["_auth_user_backend"]
        # get key from backend class name
        auth_method = get_matching_authmethod(backend)
        try:
            user_auth = UserAuthentication.objects.get(
                username=user.username, authenticationMethod=auth_method
            )
            if not user_auth.approved:
                return True
        except UserAuthentication.DoesNotExist:
            return False

    return False


def get_matching_authmethod(backend):
    for authKey, _, authBackend in settings.AUTH_PROVIDERS:
        if backend == authBackend:
            return authKey
    if backend == "django.contrib.auth.backends.ModelBackend":
        return settings.DEFAULT_AUTH  # 'localdb'
    return None
