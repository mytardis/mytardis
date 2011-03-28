# -*- coding: utf-8 -*-

from django.db import models

from tardis.tardis_portal.models import Dataset


class Equipment(models.Model):
    key = models.CharField(unique=True, max_length=30)
    dataset = models.ManyToManyField(Dataset, null=True, blank=True)
    description = models.TextField(blank=True)
    make = models.CharField(max_length=60, blank=True)
    model = models.CharField(max_length=60, blank=True)
    type = models.CharField(max_length=60, blank=True)
    serial = models.CharField(max_length=60, blank=True)
    comm = models.DateField(null=True, blank=True)
    decomm = models.DateField(null=True, blank=True)
    url = models.URLField(null=True, blank=True, verify_exists=False, max_length=255)

    def __unicode__(self):
        return self.key
