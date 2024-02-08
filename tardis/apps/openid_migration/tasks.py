import logging

from django.conf import settings
from django.contrib.auth.models import User

from celery import shared_task

from tardis import default_settings

from .email_text import email_migration_success

logger = logging.getLogger(__name__)


@shared_task
def notify_migration_status(user_id, new_username, new_authmethod):

    user = User.objects.get(id=user_id)
    subject, message_content = email_migration_success(
        user, new_username, new_authmethod
    )
    try:
        user.email_user(
            subject,
            message_content,
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", default_settings.DEFAULT_FROM_EMAIL
            ),
            fail_silently=True,
        )
        logger.info("email sent")
    except Exception as e:
        logger.error("failed to send migration notification email(s): %s" % repr(e))
