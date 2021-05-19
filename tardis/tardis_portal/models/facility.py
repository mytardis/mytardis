from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group


class Facility(models.Model):
    """
    Represents a facility that produces data.

    Each :class:`~tardis.tardis_portal.models.instrument.Instrument` record
    must belong to exactly one facility.  Many
    :class:`~tardis.tardis_portal.models.instrument.Instrument`
    records can be associated with the same facility.

    :attribute name: The name of the facility, e.g. "Test Facility"
    :attribute manager_group: The group of users who can access the \
        Facility Overview for this facility.
    """

    name = models.CharField(max_length=100)
    created_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    modified_time = models.DateTimeField(null=True, blank=True)
    manager_group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'Facilities'
        ordering = ('name',)

    # pylint: disable=W0222
    def save(self, *args, **kwargs):
        self.modified_time = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


def is_facility_manager(user):
    '''
    Returns true if the user manages one or more facilities
    '''
    return bool(facilities_managed_by(user).count())


def facilities_managed_by(user):
    '''
    Returns a list of facilities managed by a user
    '''
    if not user.is_authenticated:
        return Facility.objects.none()
    return Facility.objects.filter(manager_group__user=user)
