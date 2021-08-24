import logging
from os import path

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from django.utils import timezone

from ..managers import OracleSafeManager, SafeManager
from .storage import StorageBox

from .experiment import Experiment
from .instrument import Instrument

logger = logging.getLogger(__name__)


class Dataset(models.Model):
    """A dataset represents a collection files usually associated
    with a folder on an instrument PC.  Each file within the dataset is
    represented by a :class:`tardis.tardis_portal.models.DataFile`
    record.  A dataset can appear in one or more
    :class:`~tardis.tardis_portal.models.experiment.Experiment` records.
    Access controls are configured either at the ``Experiment`` level, or at
    the ``Dataset`` level, depending on MyTardis settings, by creating
    :class:`~tardis.tardis_portal.models.access_control.ExperimentACL` records or
    :class:`~tardis.tardis_portal.models.access_control.DatasetACL` records.
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
    safe = SafeManager()  # The acl-aware specific manager.

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['-id']

    # pylint: disable=W0222
    def save(self, *args, **kwargs):
        self.modified_time = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_online(self):
        return all(df.is_online for df in self.datafile_set.all())

    @property
    def online_files_count(self):
        if 'tardis.apps.hsm' in settings.INSTALLED_APPS:
            from tardis.apps.hsm.check import dataset_online_count
            return dataset_online_count(self)
        return self.datafile_set.count()

    def getParameterSets(self, schemaType=None):
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

    def get_datafiles(self, user):
        from .datafile import DataFile
        if settings.ONLY_EXPERIMENT_ACLS:
            return DataFile.objects.filter(dataset__id=self.id)
        return DataFile.safe.all(user).filter(dataset__id=self.id)

    def get_absolute_url(self):
        """Return the absolute url to the current ``Dataset``"""
        return reverse(
            'tardis_portal.view_dataset',
            kwargs={'dataset_id': self.id})

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

    def get_edit_url(self):
        """Return the absolute url to the edit view of the current
        ``Dataset``
        """
        return reverse(
            'tardis.tardis_portal.views.edit_dataset',
            args=[self.id])

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

    def get_size(self, user):
        from .datafile import DataFile
        return DataFile.sum_sizes(self.get_datafiles(user))

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
            file_objects__datafile__dataset=self).distinct()
        return boxes

    def get_ct(self):
        return ContentType.objects.get_for_model(self)

    def get_dir_tuples(self, user, basedir=""):
        """
        List the directories immediately inside basedir.

        If basedir is empty (the default), list directories with no
        separator, e.g. "subdir1"

        If basedir is a string without a separator (e.g. "subdir1"),
        look for directory paths with one separator e.g. "subdir1/subdir2"
        and include a ".." for navigating back to the dataset's top-level
        directory.

        Continuing the example from the _dirs property method:

        test files/subdir1/
        test files/subdir2/
        test files/subdir3/
        test files/subdir3/subdir4/

        List directories in the dataset's top level directory:
        >>> ds.get_dir_tuples(user, "")
        [('test files')]

        List directories within the dataset's "test files" directory:
        >>> ds.get_dir_tuples(user, "test files")
        [('..', 'test files'), ('subdir1', 'test /filessubdir1'),
         ('subdir2', 'test files/subdir2'), ('subdir3', 'test files/subdir3')]

        Request directories within a non-existent directory:
        >>> ds.get_dir_tuples(user, "test file")
        []

        List directories within the dataset's "test files/subdir3" directory:
        >>> ds.get_dir_tuples(user, "test files/subdir3")
        [('..', 'test files/subdir3'), ('subdir4', 'test files/subdir3/subdir4')]

        List directories within the dataset's "test files/subdir3/subdir4" directory:
        >>> ds.get_dir_tuples(user, "test files/subdir3/subdir4")
        [('..', 'test files/subdir3/subdir4')]
        """
        #from .datafile import DataFile

        dir_tuples = []
        if basedir:
            dir_tuples.append(('..', basedir))
        dirs_query = self.get_datafiles(user)
        if basedir:
            dirs_query = dirs_query.filter(directory__startswith='%s/' % basedir)
        dir_paths = set(dirs_query.values_list('directory', flat=True))
        for dir_path in dir_paths:
            if not dir_path:
                continue
            if basedir:
                dir_name = dir_path[len(basedir)+1:].lstrip('/').split('/')[0]
            else:
                dir_name = dir_path.split('/')[0]
            # Reconstruct the dir_path, eliminating subdirs within dir_name:
            dir_path = '/'.join([basedir, dir_name]).lstrip('/')
            dir_tuple = (dir_name, dir_path)
            if dir_name and dir_tuple not in dir_tuples:
                dir_tuples.append((dir_name, dir_path))

        return sorted(dir_tuples, key=lambda x: x[0])

    def get_dir_nodes(self, dir_tuples):
        """Return child node's subdirectories in format required for tree view

        Given a list of ('subdir', 'path/to/subdir') tuples for a dataset
        directory node, return a list of {'name': 'subdir', 'children': []}
        dictionaries required for the tree view.

        Like the get_dir_tuples method, the get_dir_nodes method only lists
        files and directories immediately within the supplied basedir, so
        any subdirectories will have an empty children array.

        Continuing the example from the _dirs property method:

        test files/subdir1/
        test files/subdir2/
        test files/subdir3/
        test files/subdir3/subdir4/

        List directories in the dataset's top level directory:
        >>> dir_tuples = ds.get_dir_tuples(user, "")
        >>> ds.get_dir_nodes(dir_tuples)
        [
            {
                'name': 'test files',
                'path': '',
                'children': []
            }
        ]

        List directories within the dataset's "test files" directory:
        >>> dir_tuples = ds.get_dir_tuples(user, "test files")
        >>> ds.get_dir_nodes(dir_tuples)
        [
            {
                'name': 'subdir1',
                'path': 'test files/subdir1',
                'children': []
            },
            {
                'name': 'subdir2',
                'path': 'test files/subdir2',
                'children': []
            },
            {
                'name': 'subdir3',
                'path': 'test files/subdir3',
                'children': []
            },
        ]

        Request directories within a non-existent directory:
        >>> dir_tuples = ds.get_dir_tuples(user, "test file")
        >>> ds.get_dir_nodes(dir_tuples)
        []

        List directories within the dataset's "test files/subdir3" directory:
        >>> dir_tuples = ds.get_dir_tuples(user, "test files3/subdir3")
        >>> ds.get_dir_nodes(dir_tuples)
        [
            'name': 'subdir4',
            'path': 'test files/subdir3/subdir4',
            'children': []
        ]

        """
        dir_list = []
        for dir_tuple in dir_tuples:
            dir_name, dir_path = dir_tuple
            if dir_name == '..':
                continue
            child_dict = {
                'name': dir_name,
                'path': dir_path,
                'children': []
            }
            dir_list.append(child_dict)
        return dir_list
