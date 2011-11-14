from django.conf import settings


def tokenuser_processor(request):
    is_token_user = request.user.username == settings.TOKEN_USERNAME
    return {'is_token_user': is_token_user}
