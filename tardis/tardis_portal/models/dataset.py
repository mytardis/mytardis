import logging
from os import path

from datetime import datetime
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from ..managers import OracleSafeManager, SafeManager
from .storage import StorageBox

from .access_control import ObjectACL
from .experiment import Experiment
from .instrument import Instrument

from taggit.managers import TaggableManager

logger = logging.getLogger(__name__)


def dataset_id_default():
    return datetime.now().strftime('DTST-%Y-%M-%d-%H-%M-%S.%f')


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
    :attribute dataset_id: A unique identifier to the dataset generated at instrument.
    :attribute immutable: Whether this dataset is read-only
    """

    PUBLIC_ACCESS_NONE = 1
    PUBLIC_ACCESS_EMBARGO = 25
    PUBLIC_ACCESS_METADATA = 50
    PUBLIC_ACCESS_FULL = 100

    PUBLIC_ACCESS_CHOICES = (
        (PUBLIC_ACCESS_NONE, 'No public access (hidden)'),
        (PUBLIC_ACCESS_EMBARGO, 'Ready to be released pending embargo expiry'),
        (PUBLIC_ACCESS_METADATA, 'Public Metadata only (no data file access)'),
        (PUBLIC_ACCESS_FULL, 'Public'),
    )

    experiments = models.ManyToManyField(Experiment, related_name='datasets')
    description = models.TextField(blank=True)
    dataset_id = models.CharField(
        max_length=400, null=False, blank=False, unique=True, default=dataset_id_default)
    directory = models.CharField(blank=True, null=True, max_length=255)
    created_time = models.DateTimeField(
        null=True, blank=True, default=timezone.now)
    modified_time = models.DateTimeField(null=True, blank=True)
    immutable = models.BooleanField(default=False)
    instrument = models.ForeignKey(Instrument, null=True, blank=True,
                                   on_delete=models.CASCADE)
    embargo_until = models.DateTimeField(null=True, blank=True)
    objectacls = GenericRelation(ObjectACL)
    objects = OracleSafeManager()
    safe = SafeManager()  # The acl-aware specific manager.
    tags = TaggableManager(blank=True)
    public_access = \
        models.PositiveSmallIntegerField(choices=PUBLIC_ACCESS_CHOICES,
                                         null=False,
                                         default=PUBLIC_ACCESS_NONE)

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['-id']

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.modified_time = timezone.now()
        super().save()

    def is_embargoed(self):
        if self.embargo_until:
            if datetime.now() < self.embargo_until:
                return True
        return False

    @property
    def is_online(self):
        return all(df.is_online for df in self.datafile_set.all())

    @property
    def tags_for_indexing(self):
        """Tags for indexing

        Used in Elasticsearch indexing.
        """
        return " ".join([tag.name for tag in self.tags.all()])

    def getParameterSets(self):
        """Return the dataset parametersets associated with this
        experiment.

        """
        from .parameters import Schema
        return self.datasetparameterset_set.filter(
            schema__schema_type=Schema.DATASET)

    def getParametersforIndexing(self):
        """Returns the experiment parameters associated with this
        experiment, formatted for elasticsearch.

        """
        from .parameters import DatasetParameter, ParameterName
        paramsets = list(self.getParameterSets())
        parameter_groups = {"string": [], "numerical" : [], "datetime" : [],
                            "schemas": []}
        for paramset in paramsets:
            param_type = {1 : 'datetime', 2 : 'string', 3 : 'numerical'}
            param_glob = DatasetParameter.objects.filter(
                parameterset=paramset).all().values_list('name','datetime_value',
                'string_value','numerical_value','sensitive_metadata')
            parameter_groups['schemas'].append({'schema_id' : paramset.schema_id})
            for sublist in param_glob:
                PN_id = ParameterName.objects.get(id=sublist[0])
                param_dict = {}
                type_idx = 0
                for idx, value in enumerate(sublist[1:-1]):
                    if value not in [None, ""]:
                        param_dict['pn_id'] = str(PN_id.id)
                        param_dict['pn_name'] = str(PN_id.full_name)
                        if sublist[-1]:
                            param_dict['sensitive'] = True
                        else:
                            param_dict['sensitive'] = False

                        type_idx = idx+1

                        if type_idx == 1:
                            param_dict['value'] = value
                        elif type_idx == 2:
                            param_dict['value'] = str(value)
                        elif type_idx == 3:
                            param_dict['value'] = float(value)
                parameter_groups[param_type[type_idx]].append(param_dict)
        return parameter_groups

    def __str__(self):
        return self.description

    def get_first_experiment(self):
        return self.experiments.order_by('created_time')[:1].get()

    def get_path(self):
        return path.join(str(self.get_first_experiment().id),
                         str(self.id))

    def get_datafiles(self, user):
        from .datafile import DataFile
        return DataFile.safe.all(user, downloadable=True).filter(dataset=self)

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

    def get_size(self, user, downloadable=False):
        from .datafile import DataFile

        datafiles = DataFile.safe.all(
            user, downloadable=downloadable).filter(dataset__id=self.id)

        return DataFile.sum_sizes(datafiles)

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

    def get_owners(self):
        acls = ObjectACL.objects.filter(pluginId='django_user',
                                        content_type=self.get_ct(),
                                        object_id=self.id,
                                        isOwner=True)
        return [acl.get_related_object() for acl in acls]

    def get_users(self):
        acls = ObjectACL.objects.filter(pluginId='django_user',
                                        content_type=self.get_ct(),
                                        object_id=self.id,
                                        canRead=True,
                                        isOwner=False)
        return [acl.get_related_object() for acl in acls]

    def get_users_and_perms(self):
        acls = ObjectACL.objects.filter(pluginId='django_user',
                                        content_type=self.get_ct(),
                                        object_id=self.id,
                                        canRead=True,
                                        isOwner=False)
        ret_list = []
        for acl in acls:
            user = acl.get_related_object()
            sensitive_flg = acl.canSensitive
            download_flg = acl.canDownload
            ret_list.append([user,
                             sensitive_flg,
                             download_flg])
        return ret_list

    def get_groups(self):
        acls = ObjectACL.objects.filter(pluginId='django_group',
                                        content_type=self.get_ct(),
                                        object_id=self.id,
                                        canRead=True)
        return [acl.get_related_object() for acl in acls]

    def get_groups_and_perms(self):
        acls = ObjectACL.objects.filter(pluginId='django_group',
                                        content_type=self.get_ct(),
                                        object_id=self.id,
                                        canRead=True)
        ret_list = []
        for acl in acls:
            if not acl.isOwner:
                group = acl.get_related_object()
                sensitive_flg = acl.canSensitive
                download_flg = acl.canDownload
                ret_list.append([group,
                                 sensitive_flg,
                                 download_flg])
        return ret_list

    def get_admins(self):
        acls = ObjectACL.objects.filter(pluginId='django_group',
                                        content_type=self.get_ct(),
                                        object_id=self.id,
                                        isOwner=True)
        return [acl.get_related_object() for acl in acls]

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
        >>> ds.get_dir_tuples("")
        [('test files')]

        List directories within the dataset's "test files" directory:
        >>> ds.get_dir_tuples("test files")
        [('..', 'test files'), ('subdir1', 'test /filessubdir1'),
         ('subdir2', 'test files/subdir2'), ('subdir3', 'test files/subdir3')]

        Request directories within a non-existent directory:
        >>> ds.get_dir_tuples("test file")
        []

        List directories within the dataset's "test files/subdir3" directory:
        >>> ds.get_dir_tuples("test files/subdir3")
        [('..', 'test files/subdir3'), ('subdir4', 'test files/subdir3/subdir4')]

        List directories within the dataset's "test files/subdir3/subdir4" directory:
        >>> ds.get_dir_tuples("test files/subdir3/subdir4")
        [('..', 'test files/subdir3/subdir4')]
        """
        from .datafile import DataFile

        dir_tuples = []
        if basedir:
            dir_tuples.append(('..', basedir))
        dirs_query = DataFile.safe.all(user).filter(dataset=self)
        if basedir:
            dirs_query = dirs_query.filter(
                directory__startswith='%s/' % basedir)
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

    def get_dir_nodes(self, user, dir_tuples):
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
        >>> dir_tuples = ds.get_dir_tuples("")
        >>> ds.get_dir_nodes(dir_tuples)
        [
            {
                'name': 'test files',
                'path': '',
                'children': []
            }
        ]

        List directories within the dataset's "test files" directory:
        >>> dir_tuples = ds.get_dir_tuples("test files")
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
        >>> dir_tuples = ds.get_dir_tuples("test file")
        >>> ds.get_dir_nodes(dir_tuples)
        []

        List directories within the dataset's "test files/subdir3" directory:
        >>> dir_tuples = ds.get_dir_tuples("test files3/subdir3")
        >>> ds.get_dir_nodes(dir_tuples)
        [
            'name': 'subdir4',
            'path': 'test files/subdir3/subdir4',
            'children': []
        ]

        """
        dir_list = []
        basedir = ""
        for dir_tuple in dir_tuples:
            if dir_tuple[0] == '..':
                basedir = dir_tuple[1]
        for dir_tuple in dir_tuples:
            dir_name, dir_path = dir_tuple
            if dir_name == '..':
                continue
            subdir_tuples = self.get_dir_tuples(user, basedir=dir_path)
            child_dict = {
                'name': dir_name,
                'path': dir_path,
                'children': []
            }
            dir_list.append(child_dict)
        return dir_list

    def to_search(self):
        from tardis.apps.search.documents import DatasetDocument as DatasetDoc
        metadata = {"id":self.id,
                    "description":self.description,
                    "created_time":self.created_time,
                    "experiments":self.experiments,
                    "objectacls":self.objectacls,
                    "instrument":self.instrument,
                    "modified_time":self.modified_time,
                    "created_time":self.created_time,
                    "tags":self.tags_for_indexing,
                    "parameters":self.getParametersforIndexing()
                    }
        return DatasetDoc(meta=metadata)
