import logging

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from tardis.tardis_portal.models.experiment import Experiment
from ..base_models import PID #noqa

logger = logging.getLogger(__name__)


class ExperimentPID(PID):
    experiment = models.OneToOneField(
        Experiment, on_delete=models.CASCADE, related_name="pid"
    )


@receiver(post_save, sender=Experiment, dispatch_uid="create_experiment_pid")
def create_experiment_pid(sender, instance, created, **kwargs):
    if created:
        ExperimentPID(experiment=instance).save()
