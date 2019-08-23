import logging
from os import path

from django.conf import settings
from django.urls import reverse
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from ..managers import OracleSafeManager
from .storage import StorageBox

from .experiment import Experiment
from .instrument import Instrument

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Dataset(models.Model):
    """A dataset represents a collection files usually associated
    with a folder on an instrument PC.  Each file within the dataset is
    represented by a :class:`tardis.tardis_portal.models.DataFile`
    record.  A dataset can appear in one or more
    :class:`~tardis.tardis_portal.models.experiment.Experiment` records.
    Access controls are configured at the ``Experiment`` level by creating
    :class:`~tardis.tardis_portal.models.access_control.ObjectACL` records.
    Each dataset can be associated with an
    :class:`~tardis.tardis_portal.models.instrument.Instrument` record, but it is
    possible to create a dataset without specifying an instrument.

    :attribute experiment: A foreign key to the one ore more
       :class:`~tardis.tardis_portal.models.experiment.Experiment` records \
       which contain this dataset
    :attribute instrument: The foreign key to the instrument that generated \
        this data
    :attribute description: Description of this dataset, which usually \
        corresponds to the folder name on the instrument PC
    :attribute immutable: Whether this dataset is read-only
    """

    experiments = models.ManyToManyField(Experiment, related_name='datasets')
    description = models.TextField(blank=True)
    directory = models.CharField(blank=True, null=True, max_length=255)
    created_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    modified_time = models.DateTimeField(null=True, blank=True)
    immutable = models.BooleanField(default=False)
    instrument = models.ForeignKey(Instrument, null=True, blank=True,
                                   on_delete=models.CASCADE)
    objects = OracleSafeManager()

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['-id']

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.modified_time = timezone.now()
        super(Dataset, self).save()

    @property
    def is_online(self):
        return all(df.is_online for df in self.datafile_set.all())

    def getParameterSets(self):
        """Return the dataset parametersets associated with this
        experiment.

        """
        from .parameters import Schema
        return self.datasetparameterset_set.filter(
            schema__type=Schema.DATASET)

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
        from .datafile import DataFile, IMAGE_FILTER
        render_image_ds_size_limit = getattr(
            settings, 'RENDER_IMAGE_DATASET_SIZE_LIMIT', 0)
        if render_image_ds_size_limit and \
                self.datafile_set.count() > render_image_ds_size_limit:
            return DataFile.objects.none()
        return self.datafile_set.order_by('filename').filter(IMAGE_FILTER)\
            .filter(file_objects__verified=True).distinct()

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
