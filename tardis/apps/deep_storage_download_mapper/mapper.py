# -*- coding: utf-8 -*-
'''
File mapper that works for files stored in deep directory structures.
It recreates the structure as stored in the datafile directory
'''
import os
from urllib.parse import quote

from django.conf import settings

from tardis.tardis_portal.models.datafile import DataFile
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment


def deep_storage_mapper(obj, rootdir=None):
    """
    If rootdir is None, just return a filesystem-safe representation of the
    object, e.g. "DatasetDescription_123" or "strange %2F filename.txt"

    For now, only DataFiles are supported when rootdir is not None.

    :param obj: The model instance (DataFile, Dataset or Experiment)
                to generate a path for.
    :type obj: DataFile, Dataset or Experiment
    :param rootdir: The top-level directory name, or None
    :type rootdir: basestring
    :return: Filesystem-safe path for the object in the archive or SFTP view.
    :rtype: basestring
    :raises Exception:
    :raises NotImplementedError:
    """
    safe = settings.SAFE_FILESYSTEM_CHARACTERS
    if not rootdir:
        if isinstance(obj, DataFile):
            return quote(obj.filename, safe=safe)
        if isinstance(obj, Dataset):
            if settings.DATASET_SPACES_TO_UNDERSCORES:
                desc = obj.description.replace(' ', '_')
            else:
                desc = obj.description
            return quote("%s_%d" % (desc, obj.id), safe=safe)
        if isinstance(obj, Experiment):
            if settings.EXP_SPACES_TO_UNDERSCORES:
                title = obj.title.replace(' ', '_')
            else:
                title = obj.title
            return quote("%s_%d" % (title, obj.id), safe=safe)
        raise NotImplementedError(type(obj))

    if not isinstance(obj, DataFile):
        raise NotImplementedError(type(obj))

    datafile = obj
    dataset = datafile.dataset
    exp = dataset.get_first_experiment()
    filepath = os.path.join(dataset.directory or '',
                            quote(dataset.description, safe=safe),
                            datafile.directory or '', datafile.filename)
    if rootdir != 'datasets':
        return os.path.join(rootdir, filepath)
    if exp is not None:
        return os.path.join(exp.directory or '', exp.title, filepath)
    raise Exception
