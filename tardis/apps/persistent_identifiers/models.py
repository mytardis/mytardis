import logging

from django.conf import settings
from django.apps import apps
from django.contrib import admin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.dataset import Dataset

logger = logging.getLogger(__name__)

class PID(models.Model):
    """An abstract model that adds a PID field to an existing model

    :attribute pid: A CharField holding the chosen PID

    """
    pid = models.CharField(max_length=400,
                           null=True,
                           blank=True,
                           unique=True)

    class Meta:
        abstract = True
        app_label = 'pids'

    def __str__(self):
        return self.pid

class ExperimentPID(PID):
    experiment = models.OneToOneField("Experiment",
                                      on_delete=models.CASCADE,
                                      related_name='pid')


@receiver(post_save, sender=Experiment, dispatch_uid="create_experiment_pid")
def create_experiment_pid(sender, instance, created, **kwargs):
    if created:
        ExperimentPID(experiment=instance).save()
