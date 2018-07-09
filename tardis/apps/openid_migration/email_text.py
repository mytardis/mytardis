from django.conf import settings

from . import default_settings


def interpolate_template(template_name, **kwargs):
    openid_migration_email_messages = getattr(
        settings, 'OPENID_MIGRATION_EMAIL_MESSAGES',
        default_settings.OPENID_MIGRATION_EMAIL_MESSAGES)
    subject, template = openid_migration_email_messages[template_name]
    return subject, template.format(**kwargs)


def email_migration_success(user_name, auth_method):
    return interpolate_template('migration_complete', user_name=user_name,
                                auth_method=auth_method,
                                site_name=getattr(settings, 'SITE_TITLE', 'MyTardis'),)
