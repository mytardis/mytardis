import logging
from os import path

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from django.utils.safestring import SafeUnicode

from ..managers import OracleSafeManager, ExperimentManager
from .access_control import ObjectACL

from .license import License

logger = logging.getLogger(__name__)


class Experiment(models.Model):
    """The ``Experiment`` model inherits from :class:`django.db.models.Model`

    :attribute url: **Undocumented**
    :attribute approved: **Undocumented**
    :attribute title: the title of the experiment.
    :attribute institution_name: the name of the institution who created
       the dataset.
    :attribute start_time: **Undocumented**
    :attribute end_time: **Undocumented**
    :attribute created_time: **Undocumented**
    :attribute handle: **Undocumented**
    :attribute public: **Undocumented**
    :attribute objects: default model manager
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
    institution_name = models.CharField(max_length=400,
                                        default=settings.DEFAULT_INSTITUTION)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    handle = models.TextField(null=True, blank=True)
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
    safe = ExperimentManager()  # The acl-aware specific manager.

    class Meta:
        app_label = 'tardis_portal'

    def save(self, *args, **kwargs):
        super(Experiment, self).save(*args, **kwargs)
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

    def getParameterSets(self, schemaType=None):
        """Return the experiment parametersets associated with this
        experiment.

        """
        from .parameters import Schema
        if schemaType == Schema.EXPERIMENT or schemaType is None:
            return self.experimentparameterset_set.filter(
                schema__type=Schema.EXPERIMENT)
        else:
            raise Schema.UnsupportedType

    def __unicode__(self):
        return self.title

    def get_or_create_directory(self):
        dirname = path.join(settings.FILE_STORE_PATH,
                            str(self.id))
        if not path.exists(dirname):
            from os import chmod, mkdir
            try:
                mkdir(dirname)
                chmod(dirname, 0770)
            except:
                dirname = None
        return dirname

    @models.permalink
    def get_absolute_url(self):
        """Return the absolute url to the current ``Experiment``"""
        return ('tardis_portal.view_experiment', (),
                {'experiment_id': self.id})

    @models.permalink
    def get_edit_url(self):
        """Return the absolute url to the edit view of the current
        ``Experiment``

        """
        return ('tardis.tardis_portal.views.edit_experiment', (),
                {'experiment_id': self.id})

    @models.permalink
    def get_create_token_url(self):
        """Return the absolute url to the create token view of the current
        ``Experiment``
        """
        return ('tardis.tardis_portal.views.create_token', (),
                {'experiment_id': self.id})

    def get_datafiles(self):
        from .datafile import DataFile
        return DataFile.objects.filter(dataset__experiments=self)

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

    def get_images(self):
        from .datafile import IMAGE_FILTER
        return self.get_datafiles().order_by('-modification_time',
                                             '-created_time') \
            .filter(IMAGE_FILTER)

    def get_size(self):
        from .datafile import DataFile
        return DataFile.sum_sizes(self.get_datafiles())

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

    def get_groups(self):
        acls = ObjectACL.objects.filter(pluginId='django_group',
                                        content_type=self.get_ct(),
                                        object_id=self.id,
                                        canRead=True)
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


class ExperimentAuthor(models.Model):

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    author = models.CharField(max_length=255)
    institution = models.CharField(max_length=255,
                                   blank=True, null=True)
    email = models.CharField(max_length=255,
                             blank=True, null=True)
    order = models.PositiveIntegerField()
    url = models.URLField(
        max_length=255,
        blank=True, null=True,
        help_text="URL identifier for the author")

    def save(self, *args, **kwargs):
        super(ExperimentAuthor, self).save(*args, **kwargs)
        try:
            from .hooks import publish_public_expt_rifcs
            publish_public_expt_rifcs(self.experiment)
        except StandardError:
            logger.exception('')

    def __unicode__(self):
        return SafeUnicode(self.author) + ' | ' \
            + SafeUnicode(self.experiment.id) + ' | ' \
            + SafeUnicode(self.order)

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['order']
        unique_together = (('experiment', 'author'),)
