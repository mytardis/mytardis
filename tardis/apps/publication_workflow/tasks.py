import logging
import traceback

from celery.task import task
import CifFile
from django.conf import settings
from django.core.cache import get_cache
from django.db import transaction
from django.utils import timezone
from tardis.tardis_portal.models import Schema, Experiment, \
    ExperimentParameter, ExperimentParameterSet, \
    ParameterName
from tardis.apps.publication_workflow.doi import DOI
from tardis.apps.publication_workflow.utils import PDBCifHelper, send_mail_to_authors
from tardis.apps.publication_workflow.email_text import email_pub_released
from tardis.apps.publication_workflow import default_settings

logger = logging.getLogger(__name__)

LOCK_EXPIRE = 60 * 5  # Lock expires in 5 minutes


@task(
    name="apps.publication_workflow.update_publication_records",
    ignore_result=True)
def update_publication_records():
    cache = get_cache('celery-locks')

    # Locking functions to ensure only one worker operates
    # on publication records at a time.
    lock_id = 'pub-update-lock'
    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    if (acquire_lock()):
        try:
            populate_pdb_pub_records()
            process_embargos()
        finally:
            release_lock()


def has_pdb_embargo(publication):
    try:
        has_embargo = ExperimentParameter.objects.get(
            name__name='pdb-embargo',
            name__schema__namespace=getattr(
                settings,
                'PUBLICATION_SCHEMA_ROOT',
                default_settings.PUBLICATION_SCHEMA_ROOT),
            parameterset__experiment=publication
        ).string_value.lower() == 'true'
    except ExperimentParameter.DoesNotExist:
        has_embargo = False

    return has_embargo


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
    restricted_publications = Experiment.objects.filter(
        experimentparameterset__schema__namespace=PUB_SCHEMA,
        public_access=Experiment.PUBLIC_ACCESS_EMBARGO) \
        .exclude(
        experimentparameterset__schema__namespace=PUB_SCHEMA_DRAFT).distinct()
    for pub in restricted_publications:
        # Check the pdb-embargo record. pdb_pass is true if there
        # are no pdb restrictions.
        try:
            pdb_pass = not has_pdb_embargo(pub)
        except ExperimentParameter.DoesNotExist:
            pdb_pass = True

        # Check the embargo date
        release_date = get_release_date(pub)
        embargo_expired = timezone.now() >= release_date

        if embargo_expired and pdb_pass:
            pub.public_access = Experiment.PUBLIC_ACCESS_FULL
            doi_value = None
            if getattr(settings, 'MODC_DOI_ENABLED',
                       default_settings.MODC_DOI_ENABLED):
                try:
                    doi_value = ExperimentParameter.objects.get(
                        name__name='doi',
                        name__schema__namespace=getattr(
                            settings,
                            'PUBLICATION_DETAILS_SCHEMA',
                            default_settings.PUBLICATION_DETAILS_SCHEMA),
                        parameterset__experiment=pub).string_value
                    doi = DOI(doi_value)
                    doi.activate()
                    logger.info(
                        "DOI %s for publication id %i is now active." %
                        (doi.doi, pub.id))
                except ExperimentParameter.DoesNotExist:
                    pass

            subject, email_message = email_pub_released(pub.title, doi_value)

            send_mail_to_authors(pub, subject, email_message)
            pub.save()


@transaction.atomic
def populate_pdb_pub_records():
    PUB_SCHEMA = getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                         default_settings.PUBLICATION_SCHEMA_ROOT)
    PUB_SCHEMA_DRAFT = getattr(settings, 'PUBLICATION_DRAFT_SCHEMA',
                               default_settings.PUBLICATION_DRAFT_SCHEMA)
    PDB_SCHEMA = getattr(settings, 'PDB_PUBLICATION_SCHEMA_ROOT',
                         default_settings.PDB_PUBLICATION_SCHEMA_ROOT)
    publications = Experiment.objects \
        .filter(experimentparameterset__schema__namespace=PDB_SCHEMA) \
        .filter(experimentparameterset__schema__namespace=PUB_SCHEMA) \
        .exclude(experimentparameterset__schema__namespace=PUB_SCHEMA_DRAFT) \
        .distinct()

    last_update_parameter_name = ParameterName.objects.get(
        name='pdb-last-sync',
        schema__namespace=PUB_SCHEMA)

    def add_if_missing(parameterset, name, string_value=None,
                       numerical_value=None, datetime_value=None):
        try:
            ExperimentParameter.objects.get(
                name__name=name, parameterset=parameterset)
        except ExperimentParameter.DoesNotExist:
            param_name = ParameterName.objects.get(
                name=name, schema=parameterset.schema)
            param = ExperimentParameter(name=param_name,
                                        parameterset=parameterset)
            param.string_value = string_value
            param.numerical_value = numerical_value
            param.datetime_value = datetime_value
            param.save()

    for pub in publications:
        try:
            # try to get the last update time for the PDB data
            pdb_last_update_parameter = ExperimentParameter.objects.get(
                parameterset__schema__namespace=PUB_SCHEMA,
                name=last_update_parameter_name,
                parameterset__experiment=pub
            )
            last_update = pdb_last_update_parameter.datetime_value
            needs_update = last_update + \
                getattr(settings,
                        'PDB_REFRESH_INTERVAL',
                        default_settings.PDB_REFRESH_INTERVAL) \
                < timezone.now()

        except ExperimentParameter.DoesNotExist:
            # if the PDB last update time parameter doesn't exist,
            # we definitely need to update the data and create a last
            # update entry
            needs_update = True
            pdb_last_update_parameter = None

        # If an update needs to happen...
        if needs_update:
            # 1. get the PDB info
            pdb_parameter_set = ExperimentParameterSet.objects.get(
                schema__namespace=getattr(
                    settings,
                    'PDB_PUBLICATION_SCHEMA_ROOT',
                    default_settings.PDB_PUBLICATION_SCHEMA_ROOT),
                experiment=pub)
            pdb = ExperimentParameter.objects.get(
                name__name='pdb-id',
                parameterset=pdb_parameter_set)
            pdb_id = pdb.string_value
            # 1a. cosmetic change of case for PDB ID, if entered incorrectly
            if pdb_id != pdb_id.upper():
                pdb.string_value = pdb_id.upper()
                pdb.save()

            try:
                # 2. fetch the info from pdb.org
                pdb = PDBCifHelper(pdb_id)

                # 3. insert all standard pdb parameters
                add_if_missing(pdb_parameter_set, 'title',
                               string_value=pdb.get_pdb_title())
                add_if_missing(pdb_parameter_set, 'url',
                               string_value=pdb.get_pdb_url())
                try:
                    add_if_missing(pdb_parameter_set, 'resolution',
                                   numerical_value=pdb.get_resolution())
                except ValueError:
                    logger.error(
                        'PDB field "resolution" could not be set for '
                        'publication Id %i \n %s' %
                        (pub.id, traceback.format_exc()))

                try:
                    add_if_missing(pdb_parameter_set, 'r-value',
                                   numerical_value=pdb.get_obs_r_value())
                except ValueError:
                    logger.error(
                        'PDB field "r-value" could not be set for '
                        'publication Id %i \n %s' %
                        (pub.id, traceback.format_exc()))

                try:
                    add_if_missing(pdb_parameter_set, 'r-free',
                                   numerical_value=pdb.get_free_r_value())
                except ValueError:
                    logger.error(
                        'PDB field "r-free" could not be set for '
                        'publication Id %i \n %s' %
                        (pub.id, traceback.format_exc()))

                add_if_missing(pdb_parameter_set, 'space-group',
                               string_value=pdb.get_spacegroup())
                add_if_missing(pdb_parameter_set, 'unit-cell',
                               string_value=pdb.get_unit_cell())

                # 4. insert sequence info (lazy checking)
                pdb_seq_parameter_sets = ExperimentParameterSet.objects.filter(
                    schema__namespace=getattr(
                        settings,
                        'PDB_SEQUENCE_PUBLICATION_SCHEMA',
                        default_settings.PDB_SEQUENCE_PUBLICATION_SCHEMA),
                    experiment=pub)
                if pdb_seq_parameter_sets.count() == 0:
                    # insert seqences
                    for seq in pdb.get_sequence_info():
                        seq_ps_namespace = getattr(
                            settings,
                            'PDB_SEQUENCE_PUBLICATION_SCHEMA',
                            default_settings.PDB_SEQUENCE_PUBLICATION_SCHEMA)
                        seq_parameter_set = ExperimentParameterSet(
                            schema=Schema.objects.get(
                                namespace=seq_ps_namespace),
                            experiment=pub)
                        seq_parameter_set.save()
                        add_if_missing(seq_parameter_set, 'organism',
                                       string_value=seq['organism'])
                        add_if_missing(seq_parameter_set, 'expression-system',
                                       string_value=seq['expression_system'])
                        add_if_missing(seq_parameter_set, 'sequence',
                                       string_value=seq['sequence'])

                # 5. insert/update citation info (aggressive)
                ExperimentParameterSet.objects.filter(
                    schema__namespace=getattr(
                        settings,
                        'PDB_CITATION_PUBLICATION_SCHEMA',
                        default_settings.PDB_CITATION_PUBLICATION_SCHEMA),
                    experiment=pub).delete()
                for citation in pdb.get_citations():
                    cit_ps_namespace = getattr(
                        settings,
                        'PDB_CITATION_PUBLICATION_SCHEMA',
                        default_settings.PDB_CITATION_PUBLICATION_SCHEMA)
                    cit_parameter_set = ExperimentParameterSet(
                        schema=Schema.objects.get(namespace=cit_ps_namespace),
                        experiment=pub)
                    cit_parameter_set.save()
                    add_if_missing(cit_parameter_set, 'title',
                                   string_value=citation['title'])
                    add_if_missing(cit_parameter_set, 'authors',
                                   string_value='; '.join(citation['authors']))
                    add_if_missing(cit_parameter_set, 'journal',
                                   string_value=citation['journal'])
                    add_if_missing(cit_parameter_set, 'volume',
                                   string_value=citation['volume'])
                    add_if_missing(cit_parameter_set, 'page-range',
                                   string_value='-'.join(
                                       [citation['page_first'],
                                        citation['page_last']]))
                    add_if_missing(cit_parameter_set, 'doi',
                                   string_value='http://dx.doi.org/' +
                                                citation['doi'])

                # 6. Remove the PDB embargo if set, since the update has
                # occurred and therefore the PDB must have been relased.
                try:
                    ExperimentParameter.objects.get(
                        name__name='pdb-embargo',
                        parameterset__schema__namespace=getattr(
                            settings,
                            'PUBLICATION_SCHEMA_ROOT',
                            default_settings.PUBLICATION_SCHEMA_ROOT)).delete()
                except ExperimentParameter.DoesNotExist:
                    pass

                # 7. Set the last update parameter to be now
                if pdb_last_update_parameter is None:
                    pub_parameter_set = ExperimentParameterSet(
                        schema=Schema.objects.get(namespace=PUB_SCHEMA),
                        experiment=pub)
                    pub_parameter_set.save()
                    pdb_last_update_parameter = ExperimentParameter(
                        name=last_update_parameter_name,
                        parameterset=pub_parameter_set,
                        datetime_value=timezone.now())
                else:
                    pdb_last_update_parameter.datetime_value = timezone.now()
                pdb_last_update_parameter.save()

            except CifFile.StarError:
                # PDB is either unavailable or invalid
                # (maybe notify the user somehow?)
                continue
