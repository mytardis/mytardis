import logging

from django.conf import settings
from django.core.cache import caches
from django.db import transaction
from django.utils import timezone

from celery import shared_task  # pylint: disable=E0401

from tardis.tardis_portal.models import Experiment, ExperimentParameter
from .ardc_doi import ArdcDOI
from .utils import send_mail_to_authors
from .email_text import email_pub_released
from . import default_settings

logger = logging.getLogger(__name__)

LOCK_EXPIRE = 60 * 5  # Lock expires in 5 minutes


@shared_task(
    name="apps.publication_workflow.update_publication_records",
    ignore_result=True)
def update_publication_records():
    cache = caches['celery-locks']

    # Locking functions to ensure only one worker operates
    # on publication records at a time.
    lock_id = 'pub-update-lock'
    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    if (acquire_lock()):
        try:
            process_embargos()
        finally:
            release_lock()


def get_release_date(publication):
    try:
        release_date = ExperimentParameter.objects.get(
            name__name='embargo',
            name__schema__namespace=getattr(
                settings,
                'PUBLICATION_SCHEMA_ROOT',
                default_settings.PUBLICATION_SCHEMA_ROOT),
            parameterset__experiment=publication).datetime_value
    except ExperimentParameter.DoesNotExist:
        release_date = timezone.now()

    return release_date


@transaction.atomic
def process_embargos():
    # Restricted publications are defined as those having public access
    # levels less than PUBLIC_ACCESS_PENDING_AUTH and the
    # PUBLICATION_SCHEMA_ROOT schema, but not in draft.
    PUB_SCHEMA = getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                         default_settings.PUBLICATION_SCHEMA_ROOT)
    PUB_SCHEMA_DRAFT = getattr(settings, 'PUBLICATION_DRAFT_SCHEMA',
                               default_settings.PUBLICATION_DRAFT_SCHEMA)
    # get the doi event draft | register | publish
    doi_event = getattr(settings, 'DOI_EVENT', default_settings.DOI_EVENT)

    restricted_publications = Experiment.objects.filter(
        experimentparameterset__schema__namespace=PUB_SCHEMA,
        public_access=Experiment.PUBLIC_ACCESS_EMBARGO) \
        .exclude(
        experimentparameterset__schema__namespace=PUB_SCHEMA_DRAFT).distinct()
    for pub in restricted_publications:
        # Check the embargo date
        release_date = get_release_date(pub)
        embargo_expired = timezone.now() >= release_date
        if embargo_expired:
            pub.public_access = Experiment.PUBLIC_ACCESS_FULL
            doi_value = None
            if getattr(settings, 'DOI_MINT_ENABLED', default_settings.DOI_MINT_ENABLED):
                try:
                    doi_value = ExperimentParameter.objects.get(
                        name__name='doi',
                        name__schema__namespace=getattr(
                            settings,
                            'PUBLICATION_DETAILS_SCHEMA',
                            default_settings.PUBLICATION_DETAILS_SCHEMA),
                        parameterset__experiment=pub).string_value
                    doi = ArdcDOI()
                    doi.activate(doi_value, event=doi_event)
                    logger.info("DOI %s for publication id %i is now active." % (doi_value, pub.id))
                except ExperimentParameter.DoesNotExist:
                    pass

            try:
                subject, email_message = email_pub_released(pub.title, doi_value)
                send_mail_to_authors(pub, subject, email_message)
            except Exception as e:
                logger.error(
                    "failed to send publication notification email(s): %s" %
                    repr(e)
                )

            pub.save()
