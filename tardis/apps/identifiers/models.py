import logging

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from tardis.apps.projects.models import Institution, Project
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.facility import Facility
from tardis.tardis_portal.models.instrument import Instrument

logger = logging.getLogger(__name__)


class Identifier(models.Model):
    """A base class that holds the persistent_identifer and alternate_identifiers from which other
    classes can be subclassed.
    :attribute persistent_id: A CharField holding the chosen PID
    :attribute alternate_ids: A JSONField holding a list of alternative identifiers
    """

    persistent_id = models.CharField(max_length=400, null=True, blank=True, unique=True)
    alternate_ids = models.JSONField(null=True, blank=True, default=list)

    def __str__(self):
        if self.persistent_id:
            return self.persistent_id
        return "No Identifier"


class DatasetPID(Identifier):
    """A model that adds a PID field to an dataset model
    :attribute dataset: A OneToOneField pointing to the related Dataset
    """

    dataset = models.OneToOneField(
        Dataset, on_delete=models.CASCADE, related_name="persistent_id"
    )


@receiver(post_save, sender=Dataset, dispatch_uid="create_dataset_pid")
def create_dataset_pid(sender, instance, created, **kwargs):
    if "dataset" in settings.OBJECTS_WITH_IDENTIFIERS and created:
        DatasetPID(dataset=instance).save()


class ExperimentPID(Identifier):
    """A model that adds a PID field to an experiment model
    :attribute experiment: A OneToOneField pointing to the related Experiment
    """

    experiment = models.OneToOneField(
        Experiment, on_delete=models.CASCADE, related_name="persistent_id"
    )


@receiver(post_save, sender=Experiment, dispatch_uid="create_experiment_pid")
def create_experiment_pid(sender, instance, created, **kwargs):
    if "experiment" in settings.OBJECTS_WITH_IDENTIFIERS and created:
        ExperimentPID(experiment=instance).save()


class FacilityPID(Identifier):
    """A model that adds a PID field to an facility model
    :attribute facility: A OneToOneField pointing to the related Facility
    """

    facility = models.OneToOneField(
        Facility, on_delete=models.CASCADE, related_name="persistent_id"
    )


@receiver(post_save, sender=Facility, dispatch_uid="create_facility_pid")
def create_facility_pid(sender, instance, created, **kwargs):
    if "facility" in settings.OBJECTS_WITH_IDENTIFIERS and created:
        FacilityPID(facility=instance).save()


class InstrumentPID(Identifier):
    """A model that adds a PID field to an instrument model
    :attribute instrument: A OneToOneField pointing to the related Instrument
    """

    instrument = models.OneToOneField(
        Instrument, on_delete=models.CASCADE, related_name="persistent_id"
    )


@receiver(post_save, sender=Instrument, dispatch_uid="create_instrument_pid")
def create_instrument_pid(sender, instance, created, **kwargs):
    if "instrument" in settings.OBJECTS_WITH_IDENTIFIERS and created:
        InstrumentPID(instrument=instance).save()


class ProjectPID(Identifier):
    """A model that adds a PID field to a Project model
    :attribute project: A OneToOneField pointing to the related Project
    """

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="persistent_id"
    )

    # NB: the post_save connection is handled in the project app itself in able to ensure the
    # signal/slot connection can be made.


if "tardis.apps.projects" in settings.INSTALLED_APPS:

    def create_project_pid(instance, **kwargs):
        """Post save function to create PIDs for Projects if the identifer app
        is installed
        """
        ProjectPID(project=instance).save()

    if "project" in settings.OBJECTS_WITH_IDENTIFIERS:
        post_save.connect(create_project_pid, sender=Project)


class InstitutionPID(Identifier):
    """A model that adds a PID field to a Institution model
    :attribute institution: A OneToOneField pointing to the related Institution
    """

    institution = models.OneToOneField(
        Institution,
        on_delete=models.CASCADE,
        related_name="persistent_id",
    )

    # NB: the post_save connection is handled in the project app itself in able to ensure the
    # signal/slot connection can be made.


if "tardis.apps.projects" in settings.INSTALLED_APPS:

    def create_default_institution_pid(instance, **kwargs):
        """Post save function to create PIDs for Projects if the identifer app
        is installed
        """
        InstitutionPID(institution=instance).save()

    if "institution" in settings.OBJECTS_WITH_IDENTIFIERS:
        post_save.connect(create_default_institution_pid, sender=Institution)
