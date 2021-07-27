import logging

from django.db import models
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)


class Institution(models.Model):
    """An institution is a research institution such as a university.

    :attribute name: The human readable name of the institution
    :attribute pid: A persistent identifier defining the institution
    :attribute manager_group: A Django group with admin rights for the institution model
    :attribute url: A URL pointing to the institutions web page
    :attribute parent_institution: A ForeignKey relation to another Institution model
    """

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
    )
    pid = models.CharField(max_length=100, null=True, blank=True, unique=True)
    manager_group = models.ForeignKey(Group, on_delete=models.CASCADE)
    url = models.URLField(max_length=255, null=True, blank=True)
    parent_institution = models.ForeignKey(
        "Institution", on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.name

    def is_institution_manager(self, user):
        return self.manager_group in user_obj.groups.all()

    def has_parent(self):
        if self.parent_institution:
            return True
        else:
            return False
