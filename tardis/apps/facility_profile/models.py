import logging

from django.apps import apps
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


from tardis.tardis_portal.models.facility import Facility

logger = logging.getLogger(__name__)


class FacilityProfile(models.Model):
    """A model that adds a PID field to an experiment model

    :attribute experiment: A OneToOneField pointing to the related Experiment
    :attribute pid: A CharField holding the chosen PID

    """

    facility = models.OneToOneField(
        Facility, on_delete=models.CASCADE, related_name="profile"
    )
    url = models.URLField(max_length=255, null=True, blank=True)
    if apps.is_installed("tardis.apps.institution"):
        from tardis.apps.instution.models import Institution

        institution = models.ForeignKey(
            Institution, on_delete=models.CASCADE, null=True, blank=True
        )


@receiver(post_save, sender=Facility, dispatch_uid="create_facility_profile")
def create_facility_profile(sender, instance, created, **kwargs):
    if created:
        FacilityProfile(facility=facility).save()
