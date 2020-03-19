import logging
from os import path

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from django.utils.safestring import SafeText
from django.utils.encoding import python_2_unicode_compatible

from ..managers import OracleSafeManager#, ExperimentManager
from .access_control import ObjectACL

from .license import License

logger = logging.getLogger(__name__)

@python_2_unicode_compatible
class Project(models.Model):
    """A project is a collection of :class: '~tardis.tardis_portal.experiment.Experiment'
    records. A project can have multiple Experiments but an experiment has only one 
    Project.
    Inputs:
    =================================
    """

    PUBLIC_ACCESS_NONE = 1
    PUBLIC_ACCESS_EMBARGO = 25
    PUBLIC_ACCESS_METADATA = 50
    PUBLIC_ACCESS_FULL = 100

    PUBLIC_ACCESS_CHOICES = (
        (PUBLIC_ACCESS_NONE, 'No public access (hidden)'),
        (PUBLIC_ACCESS_EMBARGO, 'Ready to be released pending embargo expiry'),
        (PUBLIC_ACCESS_METADATA, 'Public Metadata only (no data file access)'),
        (PUBLIC_ACCESS_FULL, 'Public'),
    )
    name = models.CharField(max_length=255, null=False, blank=False)
    raid = models.CharField(max_length=255, null=False, blank=False, unique=True)
    description = models.TextField()
    locked = models.BooleanField(default=False)
    public_access = \
        models.PositiveSmallIntegerField(choices=PUBLIC_ACCESS_CHOICES,
                                         null=False,
                                         default=PUBLIC_ACCESS_NONE)
    #TODO Remove null=True on rebuild database
    owner = models.OneToOneField(User,
                                 null=True,
                                 on_delete=models.CASCADE)
    contact = models.ManyToManyField(User,
                                     related_name='contacts',
                                     null=True,
                                     blank=True)
    member = models.ManyToManyField(User,
                                    related_name='members',
                                    null=True,
                                    blank=True)
    objectacls = GenericRelation(ObjectACL)
    objects = OracleSafeManager()

    class Meta:
        app_label = 'tardis_portal'

    def save(self, *args, **kwargs):
        super(Project, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

        


