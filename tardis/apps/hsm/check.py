# -*- coding: utf-8 -*-

"""HSM check module.  Method for detecting whether a MyTardis
DataFileObject in Hierarchical Storage Management is online or
offline (on tape).
"""
import logging
import os
import subprocess  # nosec - Bandit B404: import_subprocess
import sys

from django.conf import settings
from django.core.files.storage import get_storage_class

from tardis.tardis_portal.models import DataFile
from tardis.tardis_portal.models import DataFileObject
from tardis.tardis_portal.models import StorageBox
from tardis.tardis_portal.models import StorageBoxOption

from . import default_settings
from .storage import HsmFileSystemStorage
from .utils import file_is_online


logger = logging.getLogger(__name__)


class DataFileNotVerified(Exception):
    """Exception raied when an operation is attempted on an
    unverified DataFile"""


class DataFileObjectNotVerified(Exception):
    """Exception raied when an operation is attempted on an
    unverified DataFile"""


class StorageClassNotSupportedError(Exception):
    """Exception raised when a storage class is not supported"""


def dfo_online(dfo):
    """Checks whether the underlying file of a DataFileObject is online

    Parameters
    ----------
    dfo : DataFileObject
        The DataFileObject for which to check the status

    Returns
    -------
    bool
        Status for whether dfo is online.

    Raises
    ------
    DataFileObjectNotVerified
        If dfo is unverified
    StorageClassNotSupportedError
        If the `django_storage_class` for the StorageBox of the input
        DataFileObject is not supported
    """
    if dfo.verified:
        storage_class = get_storage_class(dfo.storage_box.django_storage_class)
        if issubclass(storage_class, HsmFileSystemStorage):
            try:
                location = dfo.storage_box.options.get(key="location").value
                filepath = os.path.join(location, dfo.uri)
                return file_is_online(filepath)
            except StorageBoxOption.DoesNotExist:
                logger.debug("DataFileObject with id %s doesn't have a file"
                             "system path/location", dfo.id)
        else:
            msg = (
                "You have tried to check the online/offline status of a "
                "DataFileObject with data in a StorageBox with an "
                "unsupported django_storage_class. The required "
                "django_storage_class is "
                "'tardis.apps.hsm.storage.HsmFileSystemStorage'."
            )
            raise StorageClassNotSupportedError(msg)
    else:
        raise DataFileObjectNotVerified(
            "Cannot check online status of unverified DataFileObject: %s"
            % dfo.id)


def dataset_online_count(dataset):
    """Checks how many of a dataset's files are online

    Parameters
    ----------
    dataset : Dataset
        The Dataset for which to check the status

    Returns
    -------
    int
        The number of online files in this dataset
    """
    online_count =  DataFile.objects.filter(dataset=dataset).count()

    max_inode_file_size = getattr(
        settings, 'HSM_MAX_INODE_FILE_SIZE',
        default_settings.HSM_MAX_INODE_FILE_SIZE)

    dirs_to_scan = []

    sb_ids = [box['storage_box'] for box in DataFileObject.objects.filter(
              datafile__dataset=dataset,
              verified=True).values('storage_box').distinct()]
    for sb_id in sb_ids:
        box = StorageBox.objects.get(id=sb_id)
        storage_class = get_storage_class(box.django_storage_class)
        if not issubclass(storage_class, HsmFileSystemStorage):
            continue
        location = StorageBox.objects.get(
            id=sb_id).options.get(key='location').value
        uri_prefixes = set(
            dfo.uri.split('/')[0] for dfo in DataFileObject.objects.filter(
            datafile__dataset=dataset, storage_box__id=sb_id, verified=True))
        for uri_prefix in uri_prefixes:
            dirs_to_scan.append(os.path.join(location, uri_prefix))

    # Absolute paths to executables are used for increased security.
    # See Bandit's B607: start_process_with_partial_path
    for subdir in dirs_to_scan:
        format_option = '-f' if sys.platform == 'darwin' else '-c'
        format_string = '%b,%z' if sys.platform == 'darwin' else '%b,%s'
        p1 = subprocess.Popen(  # nosec - Bandit B602: subprocess_without_shell_equals_true
            ['/usr/bin/find', subdir, '-type', 'f', '-exec',
             '/usr/bin/stat', format_option, format_string, '{}', ';'],
            stdout=subprocess.PIPE, universal_newlines=True)
        grep = '/usr/bin/grep' if sys.platform == 'darwin' else '/bin/grep'
        p2 = subprocess.Popen(  # nosec - Bandit B603: subprocess_without_shell_equals_true
            [grep, '^0,'], stdin=p1.stdout, stdout=subprocess.PIPE,
            universal_newlines=True)
        p3 = subprocess.Popen(  # nosec - Bandit B603: subprocess_without_shell_equals_true
            [grep, '-v', '^0,0'], stdin=p2.stdout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True)
        stdout, _ = p3.communicate()
        for line in stdout.splitlines():
            _, size = line.split(',')
            if int(size) > max_inode_file_size:
                online_count -= 1

    return online_count
