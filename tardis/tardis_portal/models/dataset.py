from os import path

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from tardis.tardis_portal.managers import OracleSafeManager
from tardis.tardis_portal.models.fields import DirectoryField
from tardis.tardis_portal.models.storage import StorageBox

from .experiment import Experiment

import logging
logger = logging.getLogger(__name__)


class Dataset(models.Model):
    """Class to link datasets to experiments

    :attribute experiment: a forign key to the
       :class:`tardis.tardis_portal.models.Experiment`
    :attribute description: description of this dataset
    :attribute storage_box: link to one or many storage boxes of some type.
        storage boxes have to be the same for all files of a dataset
    """

    experiments = models.ManyToManyField(Experiment, related_name='datasets')
    description = models.TextField(blank=True)
    directory = DirectoryField(blank=True, null=True)
    immutable = models.BooleanField(default=False)
    storage_box = models.ManyToManyField(
        StorageBox, related_name='datasets')
    objects = OracleSafeManager()

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

    def get_replicas(self):
        from .replica import Replica
        return Replica.objects.filter(datafile__dataset=self)

    def get_download_urls(self):
        urls = {}
        params = (('dataset_id', self.id),)
        protocols = frozenset(self.get_replicas()
                                  .values_list('protocol', flat=True)
                                  .distinct())
        # Get built-in download links
        local_protocols = frozenset(('', 'tardis', 'file', 'http', 'https'))
        if any(p in protocols for p in local_protocols):
            view = 'tardis.tardis_portal.download.streaming_download_' \
                   'dataset'
            for comptype in getattr(settings,
                                    'DEFAULT_ARCHIVE_FORMATS',
                                    ['tgz', 'tar']):
                kwargs = dict(params+(('comptype', comptype),))
                urls[comptype] = reverse(view, kwargs=kwargs)

        # Get links from download providers
        for protocol in protocols - local_protocols:
            try:
                for module in settings.DOWNLOAD_PROVIDERS:
                    if module[0] == protocol:
                        view = '%s.download_dataset' % module[1]
                        urls[protocol] = reverse(view, kwargs=dict(params))
            except AttributeError:
                pass

        return urls

    @models.permalink
    def get_edit_url(self):
        """Return the absolute url to the edit view of the current
        ``Dataset``
        """
        return ('tardis.tardis_portal.views.edit_dataset', (self.id,))

    def get_images(self):
        from .datafile import IMAGE_FILTER
        images = self.datafile_set.order_by('filename')\
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
