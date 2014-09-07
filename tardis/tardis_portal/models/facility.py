from django.db import models
from django.contrib.auth.models import User

class Facility(models.Model):
    """
    Represents a facility that produces data
    """
    name=models.CharField(max_length=100)
    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural="Facilities"
    def __unicode__(self):
        return self.name

class FacilityManager(models.Model):
    """
    Indicates that a user manages a given facility.
    A user may manage more than one facility.
    """
    facility=models.ForeignKey(Facility)
    user=models.ForeignKey(User)
    class Meta:
        app_label = 'tardis_portal'
    def __unicode__(self):
        return '%s: %s' % (self.user.username, self.facility.name)


def isFacilityManager(user):
     """
     Returns true if the user manages one or more facilities
     """
     return bool(FacilityManager.objects.filter(user=user).count())

def facilitiesManagedBy(user):
    """
    Returns a list of facilities managed by a user
    """
    return Facility.objects.filter(facilitymanager__user=user)

