import logging

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from tardis.tardis_portal.models.dataset import Dataset
from ..base_models import PID  # noqa

logger = logging.getLogger(__name__)


class DatasetPID(PID):
    dataset = models.OneToOneField(
        Dataset, on_delete=models.CASCADE, related_name="pid"
    )


@receiver(post_save, sender=Dataset, dispatch_uid="create_dataset_pid")
def create_dataset_pid(sender, instance, created, **kwargs):
    if created:
        DatasetPID(dataset=instance).save()
