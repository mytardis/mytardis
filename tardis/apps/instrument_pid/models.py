import logging

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from tardis.tardis_portal.models.instrument import Instrument

logger = logging.getLogger(__name__)


class InstrumentPID(models.Model):
    """A model that adds a PID field to an experiment model

    :attribute experiment: A OneToOneField pointing to the related Experiment
    :attribute pid: A CharField holding the chosen PID

    """

    dataset = models.OneToOneField(
        Instrument, on_delete=models.CASCADE, related_name="pid"
    )
    pid = models.CharField(max_length=400, null=True, blank=True, unique=True)


@receiver(post_save, sender=Instrument, dispatch_uid="create_dataset_pid")
def create_dataset_pid(sender, instance, created, **kwargs):
    if created:
        InstrumentPID(dataset=instance).save()
