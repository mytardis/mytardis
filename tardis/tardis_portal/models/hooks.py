import logging

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .experiment import Experiment, ExperimentAuthor
from .parameters import ExperimentParameter, ExperimentParameterSet

logger = logging.getLogger(__name__)


# ## RIF-CS hooks ## #
def publish_public_expt_rifcs(experiment):
    try:
        providers = settings.RIFCS_PROVIDERS
    except:
        providers = None
    from ..publish.publishservice import PublishService
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
