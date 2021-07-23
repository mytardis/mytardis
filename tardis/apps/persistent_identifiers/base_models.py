import logging

from django.conf import settings
from django.apps import apps
from django.contrib import admin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

class PID(models.Model):
    """An abstract model that adds a PID field to an existing model

    :attribute pid: A CharField holding the chosen PID

    """
    pid = models.CharField(max_length = 400,
                           null = True,
                           blank = True,
                           unique = True)

    class Meta:
        abstract = True
