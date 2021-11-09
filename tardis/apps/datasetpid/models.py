import logging

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from tardis.tardis_portal.models.dataset import Dataset

logger = logging.getLogger(__name__)


class DatasetPID(models.Model):
    """A model that adds a PID field to an dataset model

    :attribute dataset: A OneToOneField pointing to the related Experiment
    :attribute pid: A CharField holding the chosen PID
    :attribute alternate_identifiers: A JSONField holding a list of alternative identifers

    """

    dataset = models.OneToOneField(
        Dataset, on_delete=models.CASCADE, related_name="pid"
    )
    pid = models.CharField(max_length=400, null=True, blank=True, unique=True)
    alternate_ids = models.JSONField(null=True, blank=True, default=list())

    def __str__(self):
        if self.pid:
            return self.pid
        return "No Identifier"


@receiver(post_save, sender=Dataset, dispatch_uid="create_dataset_pid")
def create_dataset_pid(sender, instance, created, **kwargs):
    if created:
        DatasetPID(dataset=instance).save()
