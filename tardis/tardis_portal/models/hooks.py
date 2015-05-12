from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .datafile import DataFileObject
from .experiment import Experiment, ExperimentAuthor
from .parameters import ExperimentParameter, ExperimentParameterSet

import logging
logger = logging.getLogger(__name__)


# ## RIF-CS hooks ## #
def publish_public_expt_rifcs(experiment):
    try:
        providers = settings.RIFCS_PROVIDERS
    except:
        providers = None
    from tardis.tardis_portal.publish.publishservice import PublishService
    pservice = PublishService(providers, experiment)
    try:
        pservice.manage_rifcs(settings.OAI_DOCS_PATH)
    except:
        logger.error('RIF-CS publish hook failed for experiment %d.'
                     % experiment.id)


@receiver(post_save, sender=ExperimentAuthor)
@receiver(post_delete, sender=ExperimentAuthor)
def post_save_experimentauthor(sender, **kwargs):
    experimentauthor = kwargs['instance']
    try:
        publish_public_expt_rifcs(experimentauthor.experiment)
    except Experiment.DoesNotExist:
        # If for some reason the experiment is missing, then ignore update
        pass


@receiver(post_save, sender=ExperimentParameter)
@receiver(post_delete, sender=ExperimentParameter)
def post_save_experiment_parameter(sender, **kwargs):
    experiment_param = kwargs['instance']
    try:
        publish_public_expt_rifcs(experiment_param.parameterset.experiment)
    except ExperimentParameterSet.DoesNotExist:
        # If for some reason the experiment parameter set is missing,
        # then ignore update
        pass


@receiver(post_save, sender=Experiment)
@receiver(post_delete, sender=Experiment)
def post_save_experiment(sender, **kwargs):
    experiment = kwargs['instance']
    publish_public_expt_rifcs(experiment)


# THIS MUST BE DEFINED BEFORE GENERATING RIF-CS
@receiver(post_save, sender=Experiment)
def ensure_doi_exists(sender, **kwargs):
    experiment = kwargs['instance']
    if settings.DOI_ENABLE and \
       experiment.public_access != Experiment.PUBLIC_ACCESS_NONE:
        doi_url = settings.DOI_BASE_URL + experiment.get_absolute_url()
        from tardis.tardis_portal.ands_doi import DOIService
        doi_service = DOIService(experiment)
        doi_service.get_or_mint_doi(doi_url)


@receiver(post_save, sender=DataFileObject, dispatch_uid='auto_verify_dfos')
def auto_verify_on_save(sender, **kwargs):
    '''
    auto verify local files
    reverify on every save
    '''
    dfo = kwargs['instance']
    update_fields = kwargs['update_fields']
    # if save is done by the verify action, only 'verified' is updated
    # needs to be called as .save(update_fields=['verified'])
    if update_fields is not None and \
       {'verified', 'last_verified_time'} >= set(update_fields):
        return
    dfo.verify.apply_async(countdown=5)
