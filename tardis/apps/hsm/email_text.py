from django.conf import settings
from django.contrib.sites.models import Site

from . import default_settings


def interpolate_template(template_name, **kwargs):
    hsm_email_templates = getattr(
        settings, 'HSM_EMAIL_TEMPLATES',
        default_settings.HSM_EMAIL_TEMPLATES)
    subject, template = hsm_email_templates[template_name]
    return subject.format(**kwargs), template.format(**kwargs)


def email_dfo_recall_complete(dfo, user):
    if dfo.datafile.directory:
        file_path = '/'.join([dfo.datafile.directory, dfo.datafile.filename])
    else:
        file_path = dfo.datafile.filename
    download_url = dfo.datafile.download_url
    protocol = 'https' if settings.SECURE_PROXY_SSL_HEADER else 'http'
    site = Site.objects.get_current().domain
    download_url = '%s://%s%s' % (protocol, site, download_url)
    return interpolate_template(
        'dfo_recall_complete',
        first_name=user.first_name, last_name=user.last_name,
        file_path=file_path,
        download_url=download_url,
        support_email=settings.SUPPORT_EMAIL, site_title=settings.SITE_TITLE)


def email_dfo_recall_failed(dfo, user):
    if dfo.datafile.directory:
        file_path = '/'.join([dfo.datafile.directory, dfo.datafile.filename])
    else:
        file_path = dfo.datafile.filename
    download_url = dfo.datafile.download_url
    protocol = 'https' if settings.SECURE_PROXY_SSL_HEADER else 'http'
    site = Site.objects.get_current().domain
    return interpolate_template(
        'dfo_recall_failed',
        first_name=user.first_name, last_name=user.last_name,
        file_path=file_path,
        download_url=download_url,
        support_email=settings.SUPPORT_EMAIL, site_title=settings.SITE_TITLE)
