from django.db import models
from django.utils import timezone

from .facility import Facility


class Instrument(models.Model):
    """
    Represents an instrument belonging to a facility that produces data
    """

    name = models.CharField(max_length=100)
    created_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    modified_time = models.DateTimeField(null=True, blank=True)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)

    class Meta:
        app_label = "tardis_portal"
        verbose_name_plural = "Instruments"
        unique_together = ["name", "facility"]
        ordering = ("name",)

    # pylint: disable=W0222
    def save(self, *args, **kwargs):
        self.modified_time = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def getParameterSets(self):
        """Return the instrument parametersets associated with this
        instrument.
        """
        from .parameters import Schema

        return self.instrumentparameterset_set.filter(schema__type=Schema.INSTRUMENT)

    def _has_change_perm(self, user_obj):
        """
        Instrument objects should only be modified by members of the facility
        managers group.
        """
        return self.facility.manager_group in user_obj.groups.all()
