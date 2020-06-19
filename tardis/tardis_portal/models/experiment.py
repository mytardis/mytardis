import logging
from os import path

from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from django.utils.safestring import SafeText
from django.utils.encoding import python_2_unicode_compatible
from django_elasticsearch_dsl import fields

from ..managers import OracleSafeManager, SafeManager
from .access_control import ObjectACL
from .project import Project
from .institution import Institution

from .license import License

logger = logging.getLogger(__name__)


def experiment_internal_id_default():
    return datetime.now().strftime('WUI-%Y-%M-%d-%H-%M-%S.%f')


@python_2_unicode_compatible
class Experiment(models.Model):
    """An ``Experiment`` is a collection of
    :class:`~tardis.tardis_portal.models.dataset.Dataset` records.
    A :class:`~tardis.tardis_portal.models.dataset.Dataset` record can appear
    in multiple ``Experiment`` records.  Access controls are configured at the
    ``Experiment`` level by creating
    :class:`~tardis.tardis_portal.models.access_control.ObjectACL` records.

    :attribute url: An optional URL associated with the data collection
    :attribute approved: An optional field indicating whether the collection is approved
    :attribute title: The title of the experiment.
    :attribute description: The description of the experiment.
    :attribute internal_id: Identifier generated at the instrument, for this experiment
    :attribute project_id: UoA project ID (e.g. RAID)
    :attribute start_time: **Undocumented**
    :attribute end_time: **Undocumented**
    :attribute created_time: **Undocumented**
    :attribute handle: **Undocumented**
    :attribute public: Whether the experiment is publicly accessible
    :attribute objects: Default model manager
    :attribute safe: ACL aware model manager

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

    PUBLICATION_SCHEMA_ROOT = 'http://www.tardis.edu.au/schemas/publication/'
    PUBLICATION_DETAILS_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'details/'
    PUBLICATION_DRAFT_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'draft/'

    url = models.URLField(max_length=255,
                          null=True, blank=True)
    approved = models.BooleanField(default=False)
    title = models.CharField(max_length=400)
    # institution_name = models.CharField(max_length=400,
    #                                    default=settings.DEFAULT_INSTITUTION)
    description = models.TextField(blank=True)
    raid = models.CharField(max_length=400, null=False, blank=False,
                            unique=True, default=experiment_internal_id_default)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    #handle = models.TextField(null=True, blank=True)
    locked = models.BooleanField(default=False)
    public_access = \
        models.PositiveSmallIntegerField(choices=PUBLIC_ACCESS_CHOICES,
                                         null=False,
                                         default=PUBLIC_ACCESS_NONE)
    license = models.ForeignKey(License,  # @ReservedAssignment
                                blank=True, null=True,
                                on_delete=models.CASCADE)
    objectacls = GenericRelation(ObjectACL)
    objects = OracleSafeManager()
    safe = SafeManager()  # The acl-aware specific manager.
    embargo_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'tardis_portal'

    def is_embargoed(self):
        if self.embargo_until:
            if datetime.now() < self.embargo_until:
                return True
        return False

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .hooks import publish_public_expt_rifcs
        publish_public_expt_rifcs(self)

    def is_publication_draft(self):
        return self.experimentparameterset_set.filter(
            schema__namespace=getattr(settings, 'PUBLICATION_DRAFT_SCHEMA',
                                      self.PUBLICATION_DRAFT_SCHEMA)
        ).count() > 0

    def is_publication(self):
        return self.experimentparameterset_set.filter(
            schema__namespace__startswith=getattr(
                settings, 'PUBLICATION_SCHEMA_ROOT',
                self.PUBLICATION_SCHEMA_ROOT)
        ).count() > 0

    def getParameterSets(self):
        """Return the experiment parametersets associated with this
        experiment.

        """
        from .parameters import Schema
        return self.experimentparameterset_set.filter(
            schema__schema_type=Schema.EXPERIMENT)

    def getParametersforIndexing(self):
        """Returns the experiment parameters associated with this
        experiment, formatted for elasticsearch.

        """
        from .parameters import ExperimentParameter, ParameterName
        paramsets = list(self.getParameterSets())
        parameter_list = []
        for paramset in paramsets:
            param_type_options = {1 : 'DATETIME', 2 : 'STRING',
                                  3 : 'NUMERIC'}
            param_glob = ExperimentParameter.objects.filter(
                parameterset=paramset).all().values_list('name','datetime_value',
                'string_value','numerical_value','sensitive_metadata')
            for sublist in param_glob:
                PN_id = ParameterName.objects.get(id=sublist[0]).id
                param_dict = {}
                for idx, value in enumerate(sublist[1:-1]):
                    if value is not None:
                        param_dict['pn_id'] = str(PN_id)
                        param_dict['value'] = str(value)
                        param_dict['data_type'] = param_type_options[idx+1]
                        param_dict['sensitive'] = str(sublist[-1])
                parameter_list.append(param_dict)
        return parameter_list

    def __str__(self):
        return self.title

    def get_or_create_directory(self):
        dirname = path.join(settings.FILE_STORE_PATH,
                            str(self.id))
        if not path.exists(dirname):
            from os import chmod, mkdir
            try:
                mkdir(dirname)
                chmod(dirname, 0o770)
            except:
                dirname = None
        return dirname

    def get_absolute_url(self):
        """Return the absolute url to the current ``Experiment``"""
        return reverse(
            'tardis_portal.view_experiment',
            kwargs={'experiment_id': self.id})

    def get_edit_url(self):
        """Return the absolute url to the edit view of the current
        ``Experiment``
        """
        return reverse(
            'tardis.tardis_portal.views.edit_experiment',
            kwargs={'experiment_id': self.id})

    def get_create_token_url(self):
        """Return the absolute url to the create token view of the current
        ``Experiment``
        """
        return reverse(
            'tardis.tardis_portal.views.create_token',
            kwargs={'experiment_id': self.id})

    def get_datafiles(self, user, downloadable=False):
        from .datafile import DataFile
        return DataFile.safe.all(user, downloadable=downloadable).filter(dataset__experiments=self)

    def get_download_urls(self):
        urls = {}
        view = 'tardis.tardis_portal.download.streaming_download_experiment'
        for comptype in getattr(settings,
                                'DEFAULT_ARCHIVE_FORMATS',
                                ['tgz', 'tar']):
            urls[comptype] = reverse(view, kwargs={
                'experiment_id': self.id,
                'comptype': comptype})

        return urls

    def get_images(self, user):
        from .datafile import IMAGE_FILTER
        return self.get_datafiles(user).order_by('-modification_time',
                                                 '-created_time') \
            .filter(IMAGE_FILTER)

    def get_size(self, user, downloadable=False):
        from .datafile import DataFile
        return DataFile.sum_sizes(self.get_datafiles(user, downloadable=downloadable))

    @classmethod
    def public_access_implies_distribution(cls, public_access_level):
        '''
        Determines if a level of public access implies that distribution should
        be allowed, or alternately if it should not be allowed. Used to
        prevent free-distribution licences for essentially private data, and
        overly-restrictive licences for public data.
        '''
        return public_access_level > cls.PUBLIC_ACCESS_METADATA

    def public_download_allowed(self):
        '''
        instance method version of 'public_access_implies_distribution'
        '''
        return self.public_access > Experiment.PUBLIC_ACCESS_METADATA

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
                                        canRead=True)
        return [acl.get_related_object() for acl in acls]

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

    def _has_view_perm(self, user_obj):
        '''
        Called from the ACLAwareBackend class's has_perm method
        in tardis/tardis_portal/auth/authorisation.py

        Returning None means we won't override permissions here,
        i.e. we'll leave it to ACLAwareBackend's has_perm method
        to determine permissions from ObjectACLs
        '''
        if not hasattr(self, 'id'):
            return False

        if self.public_access >= self.PUBLIC_ACCESS_METADATA:
            return True

        return None

    def _has_change_perm(self, user_obj):
        '''
        Called from the ACLAwareBackend class's has_perm method
        in tardis/tardis_portal/auth/authorisation.py

        Returning None means we won't override permissions here,
        i.e. we'll leave it to ACLAwareBackend's has_perm method
        to determine permissions from ObjectACLs
        '''
        if not hasattr(self, 'id'):
            return False

        if self.locked:
            return False

        return None

    def _has_delete_perm(self, user_obj):
        '''
        Called from the ACLAwareBackend class's has_perm method
        in tardis/tardis_portal/auth/authorisation.py

        Returning None means we won't override permissions here,
        i.e. we'll leave it to ACLAwareBackend's has_perm method
        to determine permissions from ObjectACLs
        '''
        if not hasattr(self, 'id'):
            return False

        return None


@python_2_unicode_compatible
class ExperimentAuthor(models.Model):

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    author = models.CharField(max_length=255)
    institution = models.ForeignKey(Institution,
                                    blank=True,
                                    null=True,
                                    on_delete=models.CASCADE)
    email = models.CharField(max_length=255,
                             blank=True, null=True)
    order = models.PositiveIntegerField()
    url = models.URLField(
        max_length=255,
        blank=True, null=True,
        help_text="URL identifier for the author")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            from .hooks import publish_public_expt_rifcs
            publish_public_expt_rifcs(self.experiment)
        except Exception:
            logger.exception('')

    def __str__(self):
        return SafeText(self.author) + ' | ' \
            + SafeText(self.experiment.id) + ' | ' \
            + SafeText(self.order)

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['order']
        unique_together = (('experiment', 'author'),)
