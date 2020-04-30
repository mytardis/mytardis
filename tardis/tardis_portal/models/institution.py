import logging
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)

class Institution(models.Model):
    """An institution is a research institution such as a university."""

    name = models.CharField(max_length=255, null=False, blank=False, default='The University of Auckland')
    ror = models.CharField(max_length=100, null=True, blank=True, default='https://ror.org/03b94tp07')
    manager_group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        app_label = 'tardis_portal'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def is_institution_manager(self,
                               user):
        return self.manager_group in user_obj.groups.all()

