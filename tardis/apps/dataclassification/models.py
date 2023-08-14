from pprint import pprint

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

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

    class Meta:
        abstract = True
        app_label = "dataclassification"


class ProjectDataClassification(DataClassification):
    """A concrete model that holds the data classification for a project"""

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="data_classification"
    )

    class Meta:
        app_label = "dataclassification"


@receiver(post_save, sender=Project, dispatch_uid="create_project_data_classification")
def create_project_data_classification(sender, instance, created, **kwargs) -> None:
    """Function to create the data classification for a project in response to a project being created."""
    if created:
        project = instance
        classification = ProjectDataClassification(project=project)
        classification.save()


class ExperimentDataClassification(DataClassification):
    """A concrete model that holds the data classification for an experiment"""

    experiment = models.OneToOneField(
        Experiment, on_delete=models.CASCADE, related_name="data_classification"
    )

    class Meta:
        app_label = "dataclassification"


@receiver(
    post_save, sender=Experiment, dispatch_uid="create_experiment_data_classification"
)
def create_experiment_data_classification(sender, instance, created, **kwargs) -> None:
    """Function to create the data classfication for an experiment in response to an experiment being created

    Args:
        sender (_type_): The sender of the signal
        instance (_type_): The experiment that has been created
        created (_type_): A boolean flag that indicates if the instance has been created

    Returns:
        _type_: None
    """
    pprint("In post save receiver")
    if created:
        data_classification = kwargs.pop(
            "classification", get_classification_from_parents(instance)
        )
        pprint(data_classification)
        classification = ExperimentDataClassification(
            experiment=instance, classification=data_classification
        )
        classification.save()
        pprint(classification)
        pprint("ending post save reciever")


class DatasetDataClassification(DataClassification):
    """A concrete model that holds the data classification for a project"""

    dataset = models.OneToOneField(
        Dataset, on_delete=models.CASCADE, related_name="data_classification"
    )

    class Meta:
        app_label = "dataclassification"


@receiver(post_save, sender=Dataset, dispatch_uid="create_dataset_data_classification")
def create_dataset_data_classification(sender, instance, created, **kwargs) -> None:
    """Function to create the data classfication for a dataset in response to a dataset being created

    Args:
        sender (_type_): The sender of the signal
        instance (_type_): The dataset that has been created
        created (_type_): A boolean flag that indicates if the instance has been created

    Returns:
        _type_: None
    """
    if created:
        data_classification = kwargs.pop(
            "classification", get_classification_from_parents(instance)
        )
        classification = DatasetDataClassification(
            dataset=instance, classification=data_classification
        )
        classification.save()


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


def get_classification_from_parents(obj: Experiment | Dataset) -> int:
    """Helper funtion to get data classification from the parent object if it is not defined

    Args:
        obj (Experiment | Dataset): an instance of either an experiment or a dataset to check the parent of

    Returns:
        int: the data classification of the parent class or the most restrictive if multiple parents exist
    """
    parents = (
        obj.projects.all() if isinstance(obj, Experiment) else obj.experiments.all()
    )
    if parents:
        if classifications := [
            parent.data_classification.classification for parent in parents
        ]:
            return min(classifications)
    return DATA_CLASSIFICATION_SENSITIVE
