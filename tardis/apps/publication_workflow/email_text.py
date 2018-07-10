from django.conf import settings

from . import default_settings


def interpolate_template(template_name, **kwargs):
    publication_email_messages = getattr(
        settings, 'PUBLICATION_EMAIL_MESSAGES',
        default_settings.PUBLICATION_EMAIL_MESSAGES)
    subject, template = publication_email_messages[template_name]
    return subject, template.format(**kwargs)


def email_pub_rejected(pub_title, message=None):
    subject, email_message = interpolate_template(
        'rejected', pub_title=pub_title)

    if message:
        email_message += ''' ---
%s''' % message

    return subject, email_message


def email_pub_reverted_to_draft(pub_title, message=None):
    subject, email_message = interpolate_template(
        'reverted_to_draft', pub_title=pub_title)

    if message:
        email_message += ''' ---
%s''' % message

    return subject, email_message


def email_pub_released(pub_title, doi=None):
    if doi:
        subject, message = interpolate_template(
            'released_with_doi', pub_title=pub_title, doi=doi)
    else:
        subject, message = interpolate_template(
            'released', pub_title=pub_title)

    return subject, message

def email_pub_retracted(pub_title, message=None):
    subject, email_message = interpolate_template(
        'retracted', pub_title=pub_title)

    if message:
        email_message += ''' ---
%s''' % message

    return subject, email_message
