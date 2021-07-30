import logging

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from tardis.tardis_portal.models.facility import Facility

logger = logging.getLogger(__name__)


class FacilityPID(models.Model):
    """A model that adds a PID field to an experiment model

    :attribute experiment: A OneToOneField pointing to the related Experiment
    :attribute pid: A CharField holding the chosen PID

    """

    facility = models.OneToOneField(
        Facility, on_delete=models.CASCADE, related_name="pid"
    )
    pid = models.CharField(max_length=400, null=True, blank=True, unique=True)

    class Meta:
        app_label = "facilitypid"

    def __str__(self):
        return self.pid


@receiver(post_save, sender=Facility, dispatch_uid="create_facility_pid")
def create_facility_pid(sender, instance, created, **kwargs):
    if created:
        FacilityPID(facility=instance).save()
