import logging

from django.conf import settings
from django.db import models

from tardis.apps.projects.models import Project
from tardis.tardis_portal.models.datafile import DataFile
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.storage import StorageBox

logger = logging.getLogger(__name__)


class ProjectAutoArchive(models.Model):
    """Add an autoarchive offset field to the project model to act as an offset to the
    creation date for archiving data.

    If there are no projects, then this model should be deprecated in preference for an
    experiment level model.

    :attribute project: The project that the offset is to be stored on.
    :attribute offest: The number of days that need to be added to the creation date
        to define when the datafile can be auto archived.
    :attribute delete_offset" The number of days after the creation date that the datafile
        can be deleted.
    :attribute archives: A M2M relationship to the project archive storage boxes.
    :attribute active_stores: A M2M relationship to the project active storage boxes.
    """

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="autoarchive"
    )
    offset = models.PositiveIntegerField(
        null=False, blank=False, default=settings.AUTOARCHIVE_OFFSET
    )
    delete_offset = models.PositiveIntegerField(null=False, blank=False, default=-1)
    archives = models.ManyToManyField(
        StorageBox,
        related_name="project_archives",
    )
    active_stores = models.ManyToManyField(
        StorageBox, related_name="project_active_stores"
    )


class ExperimentAutoArchive(models.Model):
    """Add an autoarchive offset field to the project model to act as an offset to the
    creation date for archiving data.

    If there are no projects, then this model should be deprecated in preference for an
    experiment level model.

    :attribute project: The project that the offset is to be stored on.
    :attribute offest: The number of days that need to be added to the creation date
        to define when the datafile can be auto archived.
    :attribute delete_offset" The number of days after the creation date that the datafile
        can be deleted.
    :attribute archives: A M2M relationship to the experiment archive storage boxes.
    :attribute active_stores: A M2M relationship to the experiment active storage boxes.
    """

    experiment = models.OneToOneField(
        Experiment, on_delete=models.CASCADE, related_name="autoarchive"
    )
    offset = models.PositiveIntegerField(
        null=False, blank=False, default=settings.AUTOARCHIVE_OFFSET
    )
    delete_offset = models.PositiveIntegerField(null=False, blank=False, default=-1)
    archives = models.ManyToManyField(
        StorageBox,
        related_name="experiment_archives",
    )
    active_stores = models.ManyToManyField(
        StorageBox, related_name="experiment_active_stores"
    )


class DataFileAutoArchive(models.Model):
    """A concrete model that holds the metadata necessary to automatically archive the
    datafile when the appropriate time has been reached.
    :attribute datafile: The DataFile record to be archived
    :attribute archive_date: The date that the datafile should be archived on
    :attribute delete_date: An optional date field that can be used to delete the datafile
         completely
    :attribute archives: A many-to-many link that ties the archive storage boxes to the
         datafile.
    :attribute active_stores: A many-to-many link that ties the active storage boxes to the
         datafile.
    :attribute archived: A Boolean field indicating if the datafile has been archived.
    :attribute deleted: A Boolean field indicating if the datafile has been deleted.
    """

    datafile = models.OneToOneField(
        DataFile, on_delete=models.CASCADE, related_name="autoarchive"
    )
    archive_date = models.DateField(null=False, blank=False)
    delete_date = models.DateField(null=True, blank=True)
    archived = models.BooleanField(null=False, blank=False, default=False)
    deleted = models.BooleanField(null=False, blank=False, default=False)
    archives = models.ManyToManyField(
        StorageBox,
        related_name="archives",
    )
    active_stores = models.ManyToManyField(StorageBox, related_name="active_stores")


def copy_to_archive(self, verified_only: bool = True) -> bool:
    datafile = self.datafile
    archives = self.archives.all()
    archive_sboxes = {sbox.name: sbox for sbox in archives}
    if verified_only:
        obj_query = datafile.file_objects.filter(verified=True)
    else:
        obj_query = datafile.file_objects.all()
    all_objs = {dfo.storage_box.name: dfo for dfo in obj_query}
    if not all_objs:
        # TODO: Log error and handle
        logger.info(f"No datafile objects found for {datafile.filename}")
        return False
    primary_dfo = datafile.get_preferred_dfo(verified_only)
    for archive, sbox in archive_sboxes:
        if archive not in all_objs.keys():
            logger.info(f"Copying {datafile.filename} to StorageBox: {archive}")
            primary_dfo.copy_file(sbox, verify=True)
    return True


def archive(self, verified_only: bool = True) -> None:
    """A function called to archive the datafile. The function iterates through the
    datafile objects in the datafile and gets their storage boxes.

    For any storage box in the archives field, that doesn't have a DFO, a copy of the DFO
    will be made and verified.

    After ensuring that DFOs are present in the archives storage boxes, any other DFOs that
    are NOT in storage boxes in the archives are deleted.
    """
    datafile = self.datafile
    archived = self.copy_to_archive(verified_only)
    if archived:
        archives = self.archives.all()
        archive_sboxes = [sbox.name for sbox in archives]
        obj_query = datafile.file_objects.all()
        all_objs = [dfo for dfo in obj_query]
        for obj in all_objs:
            if obj.storage_box.name not in archive_sboxes:
                obj.delete()
        self.archived = True
