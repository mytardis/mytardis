import logging

from celery.task import task

from django.conf import settings

from .email_text import email_migration_success
from . import default_settings

logger = logging.getLogger(__name__)


@task
def notify_migration_status(user, old_username, new_authmethod):
    subject, message_content = email_migration_success(old_username, new_authmethod)
    try:
        user.email_user(subject,
                        message_content,
                        from_email=getattr(settings, 'OPENID_NOTIFICATION_SENDER_EMAIL',
                                           default_settings.OPENID_NOTIFICATION_SENDER_EMAIL),
                        fail_silently=True)
        logger.info("email sent")
    except Exception as e:
        logger.error(
            "failed to send migration notification email(s): %s" %
            repr(e)
        )
