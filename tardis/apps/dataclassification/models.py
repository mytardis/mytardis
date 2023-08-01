from django.db import models

from tardis.apps.projects.models import Project
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment

DATA_CLASSIFICATION_RESTRICTED = 1
DATA_CLASSIFICATION_SENSITIVE = 25
DATA_CLASSIFICATION_INTERNAL = 50
DATA_CLASSIFICATION_PUBLIC = 100


class DataClassification(models.Model):
    """A model that holds a data classification to be related to a
    MyTardis object
    :attribute classification: A PositiveSmallIntegerField containing an
    enumerated data classification"""

    DATA_CLASSIFICATION_CHOICES = (
        (DATA_CLASSIFICATION_RESTRICTED, "Restricted"),
        (DATA_CLASSIFICATION_SENSITIVE, "Sensitive"),
        (DATA_CLASSIFICATION_INTERNAL, "Internal"),
        (DATA_CLASSIFICATION_PUBLIC, "Public"),
    )

    classification = models.PositiveSmallIntegerField(
        choices=DATA_CLASSIFICATION_CHOICES,
        null=False,
        default=DATA_CLASSIFICATION_SENSITIVE,
    )


class ProjectDataClassification(DataClassification):
    """A concrete model that holds the data classification for a project"""

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="data_classification"
    )


class ExperimentDataClassification(DataClassification):
    """A concrete model that holds the data classification for an experiment"""

    experiment = models.OneToOneField(
        Experiment, on_delete=models.CASCADE, related_name="data_classification"
    )


class DatasetDataClassification(DataClassification):
    """A concrete model that holds the data classification for a project"""

    dataset = models.OneToOneField(
        Dataset, on_delete=models.CASCADE, related_name="data_classification"
    )


def classification_to_string(classification: int) -> str:
    """Helper function to turn the classification into a String

    Note: Relies on the order of operations in order to distinguish between
    PUBLIC and INTERNAL. Any PUBLIC data should have been filtered out prior to
    testing the INTERNAL classification, which simplifies the function."""
    if classification < DATA_CLASSIFICATION_SENSITIVE:
        return "Restricted"
    if classification >= DATA_CLASSIFICATION_PUBLIC:
        return "Public"
    if classification >= DATA_CLASSIFICATION_INTERNAL:
        return "Internal"
    return "Sensitive"
