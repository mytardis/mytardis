from os import path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.safestring import SafeUnicode

from tardis.tardis_portal.managers import OracleSafeManager, ExperimentManager

from .license import License

import logging
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
    PUBLIC_ACCESS_METADATA = 50
    PUBLIC_ACCESS_FULL = 100

    PUBLIC_ACCESS_CHOICES = (
        (PUBLIC_ACCESS_NONE,        'No public access (hidden)'),
        (PUBLIC_ACCESS_METADATA,    'Metadata only (no data file access)'),
        (PUBLIC_ACCESS_FULL,        'Everything'),
    )

    url = models.URLField(verify_exists=False, max_length=255,
                          null=True, blank=True)
    approved = models.BooleanField()
    title = models.CharField(max_length=400)
    institution_name = models.CharField(max_length=400,
            default=settings.DEFAULT_INSTITUTION)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User)
    handle = models.TextField(null=True, blank=True)
    locked = models.BooleanField()
    public_access = \
        models.PositiveSmallIntegerField(choices=PUBLIC_ACCESS_CHOICES,
                                         null=False,
                                         default=PUBLIC_ACCESS_NONE)
    license = models.ForeignKey(License, #@ReservedAssignment
                                blank=True, null=True)
    objects = OracleSafeManager()
    safe = ExperimentManager()  # The acl-aware specific manager.

    class Meta:
        app_label = 'tardis_portal'

    def save(self, *args, **kwargs):
        super(Experiment, self).save(*args, **kwargs)
        from .hooks import publish_public_expt_rifcs
        publish_public_expt_rifcs(self)

    def getParameterSets(self, schemaType=None):
        """Return the experiment parametersets associated with this
        experiment.

        """
        from tardis.tardis_portal.models.parameters import Schema
        if schemaType == Schema.EXPERIMENT or schemaType is None:
            return self.experimentparameterset_set.filter(
                schema__type=Schema.EXPERIMENT)
        else:
            raise Schema.UnsupportedType

    def __unicode__(self):
        return self.title

    def get_absolute_filepath(self):
        """Return the absolute storage path
        to the current ``Experiment``"""
        store = settings.FILE_STORE_PATH
        return path.join(store, str(self.id))

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
        return ('tardis.tardis_portal.views.view_experiment', (),
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

    def get_download_urls(self, comptype="zip"):
        from .datafile import Dataset_File
        urls = {}
        kwargs = {'experiment_id': self.id,
                  'comptype': comptype}
        distinct = Dataset_File.objects.filter(dataset__experiments=self.id)\
            .values('protocol').distinct()
        for key_value in distinct:
            protocol = key_value['protocol']
            if protocol in ['', 'tardis', 'file', 'http', 'https']:
                view = 'tardis.tardis_portal.download.download_experiment'
                if not '' in urls:
                    urls[''] = reverse(view, kwargs=kwargs)
            else:
                try:
                    for module in settings.DOWNLOAD_PROVIDERS:
                        if module[0] == protocol:
                            view = '%s.download_experiment' % module[1]
                            urls[protocol] = reverse(view, kwargs=kwargs)
                except AttributeError:
                    pass

        return urls

    @classmethod
    def public_access_implies_distribution(cls, public_access_level):
        '''
        Determines if a level of public access implies that distribution should
        be allowed, or alternately if it should not be allowed. Used to
        prevent free-distribution licences for essentially private data, and
        overly-restrictive licences for public data.
        '''
        return public_access_level > cls.PUBLIC_ACCESS_METADATA

    def get_owners(self):
        acls = ExperimentACL.objects.filter(pluginId='django_user',
                                            experiment=self,
                                            isOwner=True)
        return [acl.get_related_object() for acl in acls]


class ExperimentACL(models.Model):
    """The ExperimentACL table is the core of the `Tardis
    Authorisation framework
    <http://code.google.com/p/mytardis/wiki/AuthorisationEngineAlt>`_

    :attribute pluginId: the the name of the auth plugin being used
    :attribute entityId: a foreign key to auth plugins
    :attribute experimentId: a forign key to the
       :class:`tardis.tardis_portal.models.Experiment`
    :attribute canRead: gives the user read access
    :attribute canWrite: gives the user write access
    :attribute canDelete: gives the user delete permission
    :attribute isOwner: the experiment owner flag.
    :attribute effectiveDate: the date when access takes into effect
    :attribute expiryDate: the date when access ceases
    :attribute aclOwnershipType: system-owned or user-owned.

    System-owned ACLs will prevent users from removing or
    editing ACL entries to a particular experiment they
    own. User-owned ACLs will allow experiment owners to
    remove/add/edit ACL entries to the experiments they own.

    """

    OWNER_OWNED = 1
    SYSTEM_OWNED = 2
    __COMPARISON_CHOICES = (
        (OWNER_OWNED, 'Owner-owned'),
        (SYSTEM_OWNED, 'System-owned'),
    )

    pluginId = models.CharField(null=False, blank=False, max_length=30)
    entityId = models.CharField(null=False, blank=False, max_length=320)
    experiment = models.ForeignKey(Experiment)
    canRead = models.BooleanField(default=False)
    canWrite = models.BooleanField(default=False)
    canDelete = models.BooleanField(default=False)
    isOwner = models.BooleanField(default=False)
    effectiveDate = models.DateField(null=True, blank=True)
    expiryDate = models.DateField(null=True, blank=True)
    aclOwnershipType = models.IntegerField(
        choices=__COMPARISON_CHOICES, default=OWNER_OWNED)

    def get_related_object(self):
        """
        If possible, resolve the pluginId/entityId combination to a user or
        group object.
        """
        if self.pluginId == 'django_user':
            return User.objects.get(pk=self.entityId)
        return None

    def __unicode__(self):
        return '%i | %s' % (self.experiment.id, self.experiment.title)

    class Meta:
        app_label = 'tardis_portal'
        ordering = ['experiment__id']


class Author_Experiment(models.Model):

    experiment = models.ForeignKey(Experiment)
    author = models.CharField(max_length=255)
    order = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        super(Author_Experiment, self).save(*args, **kwargs)
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

