from django.db import models
from django.contrib.auth.models import Group
from django.utils.encoding import python_2_unicode_compatible


class Facility(models.Model):
    """
    Represents a facility that produces data
    """
    name = models.CharField(max_length=100)
    manager_group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'Facilities'

    @python_2_unicode_compatible
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
    return Facility.objects.filter(manager_group__user=user)
