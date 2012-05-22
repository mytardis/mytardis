from os import path

from django.conf import settings
from django.db import models

from tardis.tardis_portal.managers import OracleSafeManager

from .experiment import Experiment

import logging
logger = logging.getLogger(__name__)

class Dataset(models.Model):
    """Class to link datasets to experiments

    :attribute experiment: a forign key to the
       :class:`tardis.tardis_portal.models.Experiment`
    :attribute description: description of this dataset
    """

    experiments = models.ManyToManyField(Experiment, related_name='datasets')
    description = models.TextField(blank=True)
    immutable = models.BooleanField(default=False)
    objects = OracleSafeManager()

    class Meta:
        app_label = 'tardis_portal'

    def getParameterSets(self, schemaType=None):
        """Return the dataset parametersets associated with this
        experiment.

        """
        from tardis.tardis_portal.models.parameters import Schema
        if schemaType == Schema.DATASET or schemaType is None:
            return self.datasetparameterset_set.filter(
                schema__type=Schema.DATASET)
        else:
            raise Schema.UnsupportedType

    def addDatafile(self, filepath,
                    protocol='', url='',
                    size=None, commit=True):
        """Add Datafile helper function

        :param filepath: the file path within the repository
        :type filepath: string
        """
        from .datafile import Dataset_File
        full_file_path = path.join(settings.FILE_STORE_PATH,
                                   str(self.experiment.id),
                                   filepath)

        datafile = Dataset_File(dataset=self)
        datafile.filename = path.basename(filepath)
        if protocol:
            datafile.protocol = protocol

        if url:
            datafile.url = url
        else:
            datafile.url = 'file://' + filepath

        if size:
            datafile.size = size
        elif path.exists(full_file_path):
            datafile.size = path.getsize(full_file_path)

    def __unicode__(self):
        return self.description

    def get_first_experiment(self):
        return self.experiments.order_by('created_time')[:1].get()

    def get_absolute_filepath(self):
        return path.join(self.get_first_experiment().get_absolute_filepath(),
                         str(self.id))

    def get_images(self):
        images = self.dataset_file_set.order_by('-modification_time',
                                               '-created_time')\
                                      .filter(mimetype__startswith='image/')
        return images


