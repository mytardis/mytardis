import logging
import six

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.messages.api import MessageFailure
from django.shortcuts import redirect
from django.utils.http import urlquote

from social_core.exceptions import SocialAuthBaseException
from social_django.compat import MiddlewareMixin

logger = logging.getLogger(__name__)


class SocialAuthExceptionMiddleware(MiddlewareMixin):
    """Based on Django Social Auth's
    social_django.middleware.SocialAuthExceptionMiddleware,
    this middleware processes SocialAuthBaseExceptions and
    posts messages via Django's messages framework.

    Unlike social_django.middleware.SocialAuthExceptionMiddleware,
    this middleware doesn't add extra_tags to the messages, because
    we only want the message level ("error" or "warning") in the
    message tag to construct the "alert-error" or "alert-warning" CSS
    class in the template.
    """
    def process_exception(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        if strategy is None or self.raise_exception(request, exception):
            return None

        if isinstance(exception, SocialAuthBaseException):
            backend = getattr(request, 'backend', None)
            backend_name = getattr(backend, 'name', 'unknown-backend')

            message = self.get_message(request, exception)
            url = self.get_redirect_uri(request, exception)

            if apps.is_installed('django.contrib.messages'):
                logger.info(message)
                try:
                    messages.error(request, message)
                except MessageFailure:
                    if url:
                        url += ('?' in url and '&' or '?') + \
                               'message={0}&backend={1}'.format(urlquote(message),
                                                                backend_name)
            else:
                logger.error(message)

            if url:
                return redirect(url)

        return None

    def raise_exception(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        if strategy is not None:
            return strategy.setting('RAISE_EXCEPTIONS') or settings.DEBUG
        return None

    def get_message(self, request, exception):
        return six.text_type(exception)

    def get_redirect_uri(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        return strategy.setting('LOGIN_ERROR_URL')
