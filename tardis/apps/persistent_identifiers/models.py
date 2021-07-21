from django.apps import apps
from django.contrib import admin
from django.db import models
import uuid

from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.datafile import DataFile

logger = logging.getLogger(__name__)


class ExperimentPID(models.Model):
    """An extension to the ``Experiment`` model that adds a PID field
    This field is intended to be used as an alternative identifier to the
    ``Experiment`` that is guaranteed to be both persistent and unique.

    :attribute experiment: A one-to-one relationship to the root Experiment model
    :attribute pid: A CharField holding the chosen PID

    """

    experiment = models.OneToOneField(Experiment,
                                      on_delete=models.CASCADE)
    pid = models.CharField(max_length=400,
                           null=False,
                           blank=False,
                           unique=True,
                           default=uuid.uuid4)

class DatasetPID(models.Model):
    """An extension to the ``Dataset`` model that adds a PID field
    This field is intended to be used as an alternative identifier to the
    ``Dataset`` that is guaranteed to be both persistent and unique.

    :attribute dataset: A one-to-one relationship to the root Experiment model
    :attribute pid: A CharField holding the chosen PID

    """

    dataset = models.OneToOneField(Datasett,
                                   on_delete=models.CASCADE)
    pid = models.CharField(max_length=400,
                           null=False,
                           blank=False,
                           unique=True,
                           default=uuid.uuid4)
