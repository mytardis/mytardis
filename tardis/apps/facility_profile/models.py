import logging

from django.conf import settings
from django.apps import apps
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


from tardis.tardis_portal.models.facility import Facility

logger = logging.getLogger(__name__)


class FacilityProfile(models.Model):
    """ """

    facility = models.OneToOneField(
        Facility, on_delete=models.CASCADE, related_name="profile"
    )
    url = models.URLField(max_length=255, null=True, blank=True)
    institution = models.ForeignKey(
        settings.FACILITY_PROFILE_INSTITUTION,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )


@receiver(post_save, sender=Facility, dispatch_uid="create_facility_profile")
def create_facility_profile(sender, instance, created, **kwargs):
    if created:
        FacilityProfile(facility=facility).save()


class DefaultInstitution(models.Model):
    """Placeholder Institution model in case we aren't using a more complete
    Institution model.

    :attribute name: CharField detailing the name of the institution.
    """

    name = models.CharField(max_length=400, null=True, blank=True, unique=True)
