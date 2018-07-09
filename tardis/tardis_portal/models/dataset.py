import logging
from os import path

from django.conf import settings
from django.urls import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from ..managers import OracleSafeManager
from .storage import StorageBox

from .experiment import Experiment
from .instrument import Instrument

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Dataset(models.Model):
    """Class to link datasets to experiments

    :attribute experiment: a forign key to the
       :class:`tardis.tardis_portal.models.Experiment`
    :attribute facility: the foreign key to the facility that generated
        this data
    :attribute instrument: the foreign key to the instrument that generated
        this data
    :attribute description: description of this dataset
    """

    experiments = models.ManyToManyField(Experiment, related_name='datasets')
    description = models.TextField(blank=True)
    directory = models.CharField(blank=True, null=True, max_length=255)
    immutable = models.BooleanField(default=False)
    instrument = models.ForeignKey(Instrument, null=True, blank=True,
                                   on_delete=models.CASCADE)
    objects = OracleSafeManager()

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['-id']

    @property
    def is_online(self):
        return all(df.is_online for df in self.datafile_set.all())

    def getParameterSets(self, schemaType=None):
        """Return the dataset parametersets associated with this
        experiment.

        """
        from .parameters import Schema
        if schemaType == Schema.DATASET or schemaType is None:
            return self.datasetparameterset_set.filter(
                schema__type=Schema.DATASET)
        else:
            raise Schema.UnsupportedType

    def __str__(self):
        return self.description

    def get_first_experiment(self):
        return self.experiments.order_by('created_time')[:1].get()

    def get_path(self):
        return path.join(str(self.get_first_experiment().id),
                         str(self.id))

    def get_datafiles(self):
        from .datafile import DataFile
        return DataFile.objects.filter(dataset=self)

    @models.permalink
    def get_absolute_url(self):
        """Return the absolute url to the current ``Dataset``"""
        return ('tardis_portal.view_dataset', (),
                {'dataset_id': self.id})

    def get_download_urls(self):
        view = 'tardis.tardis_portal.download.streaming_download_' \
               'dataset'
        urls = {}
        for comptype in getattr(settings,
                                'DEFAULT_ARCHIVE_FORMATS',
                                ['tgz', 'tar']):
            urls[comptype] = reverse(view, kwargs={
                'dataset_id': self.id,
                'comptype': comptype})

        return urls

    @models.permalink
    def get_edit_url(self):
        """Return the absolute url to the edit view of the current
        ``Dataset``
        """
        return ('tardis.tardis_portal.views.edit_dataset', (self.id,))

    def get_images(self):
        from .datafile import IMAGE_FILTER
        return self.datafile_set.order_by('filename').filter(IMAGE_FILTER)

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
        from .datafile import DataFile
        return DataFile.sum_sizes(self.datafile_set)

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

    def get_all_storage_boxes_used(self):
        boxes = StorageBox.objects.filter(
            file_objects__datafile__dataset=self)
        return boxes
