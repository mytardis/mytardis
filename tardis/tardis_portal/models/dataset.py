from os import path

from django.core.urlresolvers import reverse
from django.db import models

from tardis.tardis_portal.managers import OracleSafeManager
from tardis.tardis_portal.models.fields import DirectoryField

from .experiment import Experiment

import logging
logger = logging.getLogger(__name__)

class DatasetManager(OracleSafeManager):
    """
    Added by Sindhu Emilda for natural key implementation.
    The manager for the tardis_portal's Dataset model.
    """
    # Uncomment the following commented lines before loading model Dataset.
    #def get_by_natural_key(self, description, title, username):
    def get_by_natural_key(self, description):
        """ Ideally the natural key for Dataset should be a combination of description 
        and  Experiment. But the ManyToManyField relationship manager 'ManyRelatedManager' 
        throws the exception - object has no attribute 'natural_key'. So Experiment needs
        to be commented out for loading models other than Dataset.
        """
        return self.get(description=description,
                    #experiments=Experiment.objects.get_by_natural_key(title, username), # Uncomment for loading model Dataset
        )

class Dataset(models.Model):
    """Class to link datasets to experiments

    :attribute experiment: a forign key to the
       :class:`tardis.tardis_portal.models.Experiment`
    :attribute description: description of this dataset
    """

    experiments = models.ManyToManyField(Experiment, related_name='datasets')
    description = models.TextField(blank=True)
    directory = DirectoryField(blank=True, null=True)
    immutable = models.BooleanField(default=False)
    #objects = OracleSafeManager()   # Commented by Sindhu E
    objects = DatasetManager()   # For natural key support added by Sindhu E

    ''' Added by Sindhu Emilda for natural key implementation '''
    def natural_key(self):
        """ Ideally the natural key for Dataset should be a combination of description 
        and  Experiment. But the ManyToManyField relationship manager 'ManyRelatedManager' 
        throws the exception - object has no attribute 'natural_key'. So Experiment needs
        to be commented out for loading models other than Dataset.
        """
        #return (self.description,) + self.experiments.natural_key()
        return (self.description,)
    
    #natural_key.dependencies = ['tardis_portal.Experiment'] # Uncomment for dumping model Dataset

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['-id']

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

    def __unicode__(self):
        return self.description

    def get_first_experiment(self):
        return self.experiments.order_by('created_time')[:1].get()

    def get_path(self):
        return path.join(str(self.get_first_experiment().id),
                         str(self.id))

    @models.permalink
    def get_absolute_url(self):
        """Return the absolute url to the current ``Dataset``"""
        return ('tardis.tardis_portal.views.view_dataset', (),
                {'dataset_id': self.id})

    @models.permalink
    def get_edit_url(self):
        """Return the absolute url to the edit view of the current
        ``Dataset``
        """
        return ('tardis.tardis_portal.views.edit_dataset', (self.id,))

    def get_images(self):
        from .datafile import IMAGE_FILTER
        images = self.dataset_file_set.order_by('filename')\
                                      .filter(IMAGE_FILTER)
        return images

    def _get_image(self):
        try:
            return self.get_images()[0]
        except IndexError:
            return None

    image = property(_get_image)

    def get_thumbnail_url(self):
        if self.image is None:
            return None
        return reverse('tardis.tardis_portal.iiif.download_image',
                       kwargs={'datafile_id': self.image.id,
                               'region': 'full',
                               'size': '100,',
                               'rotation': 0,
                               'quality': 'native',
                               'format': 'jpg'})

    def get_size(self):
        from .datafile import Dataset_File
        return Dataset_File.sum_sizes(self.dataset_file_set)

    def _has_any_perm(self, user_obj):
        if not hasattr(self, 'id'):
            return False
        return self.experiments.all()

    def _has_view_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_change_perm(self, user_obj):
        if self.immutable:
            return False
        return self._has_any_perm(user_obj)

    def _has_delete_perm(self, user_obj):
        if self.immutable:
            return False
        return self._has_any_perm(user_obj)
