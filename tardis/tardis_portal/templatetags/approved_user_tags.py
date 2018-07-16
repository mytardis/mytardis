from django import template
from tardis.tardis_portal.models import User,UserAuthentication

register = template.Library()


@register.filter
def check_if_user_not_approved(request):
    """
    Custom template filter to identify whether a user account
    is approved.
    """
    if request.user.is_authenticated():
        user = request.user
        try:
            user_auth = UserAuthentication.objects.get(username=user.username, authenticationMethod='Google')
            if not user_auth.approved:
                return True
        except UserAuthentication.DoesNotExist:
            return False

    return False
