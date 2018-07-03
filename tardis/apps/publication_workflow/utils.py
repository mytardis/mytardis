from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import Group

from tardis.tardis_portal.models import ExperimentAuthor

from . import default_settings


def get_pub_admin_email_addresses():
    return [
        user.email
        for user in Group.objects.get(
            name=getattr(settings, 'PUBLICATION_ADMIN_GROUP',
                         default_settings.PUBLICATION_ADMIN_GROUP))
            .user_set.all()
        if user.email]


def send_mail_to_authors(publication, subject, message, fail_silently=False):
    recipients = [author.email for author in
                  ExperimentAuthor.objects.filter(experiment=publication)]
    from_email = getattr(settings, 'PUBLICATION_NOTIFICATION_SENDER_EMAIL',
                         default_settings.PUBLICATION_NOTIFICATION_SENDER_EMAIL)
    msg = EmailMultiAlternatives(
        subject,
        message,
        from_email,
        recipients,
        cc=get_pub_admin_email_addresses())
    msg.send(fail_silently=fail_silently)
