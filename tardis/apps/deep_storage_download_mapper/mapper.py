'''
File mapper that works for files stored in deep directory structures.
It recreates the structure as stored in the datafile directory
'''
import os

from six.moves import urllib

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
            return urllib.parse.quote(obj.filename.encode('utf-8'), safe=safe)
        elif isinstance(obj, Dataset):
            if settings.DATASET_SPACES_TO_UNDERSCORES:
                desc = obj.description.replace(' ', '_')
            else:
                desc = obj.description
            return urllib.parse.quote("%s_%d" % (desc.encode('utf-8'), obj.id), safe=safe)
        elif isinstance(obj, Experiment):
            if settings.EXP_SPACES_TO_UNDERSCORES:
                title = obj.title.replace(' ', '_')
            else:
                title = obj.title
            return urllib.parse.quote("%s_%d" % (title.encode('utf-8'), obj.id), safe=safe)
        else:
            raise NotImplementedError(type(obj))

    if not isinstance(obj, DataFile):
        raise NotImplementedError(type(obj))

    datafile = obj
    dataset = datafile.dataset
    exp = dataset.get_first_experiment()
    filepath = os.path.join(dataset.directory or '',
                            urllib.parse.quote(dataset.description.encode('utf-8'),
                                  safe=safe),
                            datafile.directory or '', datafile.filename)
    if rootdir != 'datasets':
        return os.path.join(rootdir, filepath)
    elif exp is not None:
        return os.path.join(exp.directory or '', exp.title, filepath)
    else:
        raise Exception
