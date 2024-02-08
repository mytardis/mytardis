from django.conf import settings

from tardis.default_settings import site_customisations

from . import default_settings


def interpolate_template(template_name, **kwargs):
    openid_migration_email_messages = getattr(
        settings,
        "OPENID_MIGRATION_EMAIL_MESSAGES",
        default_settings.OPENID_MIGRATION_EMAIL_MESSAGES,
    )
    subject, template = openid_migration_email_messages[template_name]
    return subject.format(**kwargs), template.format(**kwargs)


def email_migration_success(user, new_username, auth_method):
    return interpolate_template(
        "migration_complete",
        firstname=user.first_name,
        lastname=user.last_name,
        user_name=new_username,
        auth_method=auth_method,
        support_email=getattr(
            settings, "SUPPORT_EMAIL", site_customisations.SUPPORT_EMAIL
        ),
        site_title=getattr(settings, "SITE_TITLE", "MyTardis"),
    )
