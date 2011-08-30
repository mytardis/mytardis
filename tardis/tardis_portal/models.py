# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
models.py

.. moduleauthor:: Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor:: Gerson Galang <gerson.galang@versi.edu.au>
.. moduleauthor:: Russell Sim <russell.sim@monash.edu>

"""

from os import path

from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User, Group
from django.utils.safestring import SafeUnicode, mark_safe
from django.dispatch import receiver

from tardis.tardis_portal.staging import StagingHook
from tardis.tardis_portal.managers import OracleSafeManager,\
    ExperimentManager, ParameterNameManager, SchemaManager


class UserProfile(models.Model):
    """
    UserProfile class is an extension to the Django standard user model.

    :attribute isDjangoAccount: is the user a local DB user
    :attribute user: a foreign key to the
       :class:`django.contrib.auth.models.User`
    """
    user = models.ForeignKey(User, unique=True)

    # This flag will tell us if the main User account was created using any
    # non localdb auth methods. For example, if a first time user authenticates
    # to the system using the VBL auth method, an account will be created for
    # him, say "vbl_user001" and the field isDjangoAccount will be set to
    # False.
    isDjangoAccount = models.BooleanField(
        null=False, blank=False, default=True)

    def getUserAuthentications(self):
        return self.userAuthentication_set.all()

    def __unicode__(self):
        return self.user.username


class GroupAdmin(models.Model):
    """GroupAdmin links the Django User and Group tables for group
    administrators

    :attribute user: a forign key to the
       :class:`django.contrib.auth.models.User`
    :attribute group: a forign key to the
       :class:`django.contrib.auth.models.Group`
    """

    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)

    def __unicode__(self):
        return '%s: %s' % (self.user.username, self.group.name)


# TODO: Generalise auth methods
class UserAuthentication(models.Model):
    CHOICES = ()
    userProfile = models.ForeignKey(UserProfile)
    username = models.CharField(max_length=50)
    authenticationMethod = models.CharField(max_length=30, choices=CHOICES)

    def __init__(self, *args, **kwargs):
        # instantiate comparisonChoices based on settings.AUTH PROVIDERS
        self.CHOICES = ()
        for authMethods in settings.AUTH_PROVIDERS:
            self.CHOICES += ((authMethods[0], authMethods[1]),)
        self._comparisonChoicesDict = dict(self.CHOICES)

        super(UserAuthentication, self).__init__(*args, **kwargs)

    def getAuthMethodDescription(self):
        return self._comparisonChoicesDict[self.authenticationMethod]

    def __unicode__(self):
        return self.username + ' - ' + self.getAuthMethodDescription()


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
    public = models.BooleanField()
    objects = OracleSafeManager()
    safe = ExperimentManager()  # The acl-aware specific manager.

    def getParameterSets(self, schemaType=None):
        """Return the experiment parametersets associated with this
        experiment.

        """
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

    def get_download_urls(self, comptype="zip"):
        urls = {}
        kwargs = {'experiment_id': self.id,
                  'comptype': comptype}
        distinct = Dataset_File.objects.filter(dataset__experiment=self.id)\
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

    def __unicode__(self):
        return '%i | %s' % (self.experiment.id, self.experiment.title)

    class Meta:
        ordering = ['experiment__id']


class Author_Experiment(models.Model):

    experiment = models.ForeignKey(Experiment)
    author = models.CharField(max_length=255)
    order = models.PositiveIntegerField()

    def __unicode__(self):
        return SafeUnicode(self.author) + ' | ' \
            + SafeUnicode(self.experiment.id) + ' | ' \
            + SafeUnicode(self.order)

    class Meta:
        ordering = ['order']
        unique_together = (('experiment', 'author'),)


class Dataset(models.Model):
    """Class to link datasets to experiments

    :attribute experiment: a forign key to the
       :class:`tardis.tardis_portal.models.Experiment`
    :attribute description: description of this dataset
    """

    experiment = models.ForeignKey(Experiment)
    description = models.TextField(blank=True)
    immutable = models.BooleanField(default=False)
    objects = OracleSafeManager()

    def getParameterSets(self, schemaType=None):
        """Return the dataset parametersets associated with this
        experiment.

        """
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

    def get_absolute_filepath(self):
        return path.join(self.experiment.get_absolute_filepath(), str(self.id))


class Dataset_File(models.Model):
    """Class to store meta-data about a physical file

    :attribute dataset: the foreign key to the
       :class:`tardis.tardis_portal.models.Dataset` the file belongs to.
    :attribute filename: the name of the file, excluding the path.
    :attribute url: the url that the datafile is located at
    :attribute size: the size of the file.
    :attribute protocol: the protocol used to access the file.
    :attribute created_time: time the file was added to tardis
    :attribute modification_time: last modification time of the file
    :attribute mimetype: for example 'application/pdf'
    :attribute md5sum: digest of length 32, containing only hexadecimal digits

    The `protocol` field is only used for rendering the download link, this
    done by insterting the protocol into the url generated to the download
    location. If the `protocol` field is blank then the `file` protocol will
    be used.
    """

    dataset = models.ForeignKey(Dataset)
    filename = models.CharField(max_length=400)
    url = models.CharField(max_length=400)
    size = models.CharField(blank=True, max_length=400)
    protocol = models.CharField(blank=True, max_length=10)
    created_time = models.DateTimeField(null=True, blank=True)
    modification_time = models.DateTimeField(null=True, blank=True)
    mimetype = models.CharField(blank=True, max_length=80)
    md5sum = models.CharField(blank=True, max_length=32)

    def getParameterSets(self, schemaType=None):
        """Return datafile parametersets associated with this experiment.

        """
        if schemaType == Schema.DATAFILE or schemaType is None:
            return self.datafileparameterset_set.filter(
                schema__type=Schema.DATAFILE)
        else:
            raise Schema.UnsupportedType

    def __unicode__(self):
        return self.filename

    def get_mimetype(self):
        if self.mimetype:
            return self.mimetype
        else:
            suffix = self.filename.split('.')[-1]
            try:
                import mimetypes
                return mimetypes.types_map['.%s' % suffix.lower()]
            except KeyError:
                return 'application/octet-stream'

    def get_download_url(self):
        view = ''
        kwargs = {'datafile_id': self.id}

        # these are the internally known protocols
        protocols = ['', 'tardis', 'file', 'http', 'https', 'ftp']
        if self.protocol in protocols:
            view = 'tardis.tardis_portal.download.download_datafile'

        # externally handled protocols
        else:
            try:
                for module in settings.DOWNLOAD_PROVIDERS:
                    if module[0] == self.protocol:
                        view = '%s.download_datafile' % module[1]
            except AttributeError:
                pass

        if view:
            return reverse(view, kwargs=kwargs)
        else:
            return ''

    def get_relative_filepath(self):
        if self.protocol == '' or self.protocol == 'tardis':
            from os.path import abspath, join
            return abspath(join(self.url.partition('://')[2]))
        elif self.protocol == 'staging':
            return self.url
        # file should refer to an absolute location
        elif self.protocol == 'file':
            return self.url.partition('://')[2]

    def get_absolute_filepath(self):
        # check for empty protocol field (historical reason) or
        # 'tardis' which indicates a location within the tardis file
        # store
        if self.protocol == '' or self.protocol == 'tardis':
            from django.conf import settings
            try:
                FILE_STORE_PATH = settings.FILE_STORE_PATH
            except AttributeError:
                return ''

            from os.path import abspath, join
            return abspath(join(FILE_STORE_PATH,
                                str(self.dataset.experiment.id),
                                str(self.dataset.id),
                                self.url.partition('://')[2]))
        elif self.protocol == 'staging':
            return self.url

        # file should refer to an absolute location
        elif self.protocol == 'file':
            return self.url.partition('://')[2]

        # ok, it doesn't look like the file is stored locally
        else:
            return ''

    def get_absolute_filepath_old(self):  # temp quickfix!
        # check for empty protocol field (historical reason) or
        # 'tardis' which indicates a location within the tardis file
        # store
        if self.protocol == '' or self.protocol == 'tardis':
            from django.conf import settings
            try:
                FILE_STORE_PATH = settings.FILE_STORE_PATH
            except AttributeError:
                return ''

            from os.path import abspath, join
            return abspath(join(FILE_STORE_PATH,
                                str(self.dataset.experiment.id),
                                self.url.partition('://')[2]))
        else:
            return ''

    def _set_size(self):

        from os.path import getsize
        self.size = str(getsize(self.get_absolute_filepath()))

    def _set_mimetype(self):

        try:
            from magic import Magic
        except:
            # TODO log that this failed
            return
        self.mimetype = Magic(mime=True).from_file(
            self.get_absolute_filepath())

    def _set_md5sum(self):

        f = open(self.get_absolute_filepath(), 'rb')
        import hashlib
        md5 = hashlib.new('md5')
        for chunk in iter(lambda: f.read(128 * md5.block_size), ''):
            md5.update(chunk)
        f.close()
        self.md5sum = md5.hexdigest()

    def deleteCompletely(self):
        import os
        filename = self.get_absolute_filepath()
        os.remove(filename)
        self.delete()


def save_DatasetFile(sender, **kwargs):

    # the object can be accessed via kwargs 'instance' key.
    df = kwargs['instance']

    if not df.get_absolute_filepath():
        return

    try:
        if not df.size:
            df._set_size()
        if not df.md5sum:
            df._set_md5sum()
        if not df.mimetype:
            df._set_mimetype()

    except IOError:
        pass
    except OSError:
        pass


pre_save.connect(save_DatasetFile, sender=Dataset_File)

staging_hook = StagingHook()
post_save.connect(staging_hook, sender=Dataset_File)


class Schema(models.Model):

    EXPERIMENT = 1
    DATASET = 2
    DATAFILE = 3
    NONE = 4
    _SCHEMA_TYPES = (
        (EXPERIMENT, 'Experiment schema'),
        (DATASET, 'Dataset schema'),
        (DATAFILE, 'Datafile schema'),
        (NONE, 'None')
    )

    namespace = models.URLField(unique=True,
                                verify_exists=False,
                                max_length=255)
    name = models.CharField(blank=True, null=True, max_length=50)
    type = models.IntegerField(
        choices=_SCHEMA_TYPES, default=EXPERIMENT)

    # subtype will be used for categorising the type of experiment, dataset
    # or datafile schemas. for example, the type of beamlines are usually used
    # further categorise the experiment, dataset, and datafile schemas. the
    # subtype might then allow for the following values: 'mx', 'ir', 'saxs'
    subtype = models.CharField(blank=True, null=True, max_length=30)
    objects = SchemaManager()

    def natural_key(self):
        return (self.namespace,)

    def _getSchemaTypeName(self, typeNum):
        return dict(self._SCHEMA_TYPES)[typeNum]

    @classmethod
    def getSubTypes(cls):
        return set([schema.subtype for schema in Schema.objects.all() \
            if schema.subtype])

    @classmethod
    def getNamespaces(cls, type, subtype=None):
        """Return the list of namespaces for equipment, sample, and experiment
        schemas.

        """
        if subtype:
            return [schema.namespace for schema in
                    Schema.objects.filter(type=type, subtype=subtype)]
        else:
            return [schema.namespace for schema in
                    Schema.objects.filter(type=type)]

    def __unicode__(self):
        return self._getSchemaTypeName(self.type) + (self.subtype and ' for ' +
            self.subtype.upper() or '') + ': ' + self.namespace

    class UnsupportedType(Exception):

        def __init__(self, msg):
            Exception.__init__(self, msg)


class DatafileParameterSet(models.Model):
    schema = models.ForeignKey(Schema)
    dataset_file = models.ForeignKey(Dataset_File)

    def __unicode__(self):
        return '%s / %s' % (self.schema.namespace, self.dataset_file.filename)

    class Meta:
        ordering = ['id']


class DatasetParameterSet(models.Model):
    schema = models.ForeignKey(Schema)
    dataset = models.ForeignKey(Dataset)

    def __unicode__(self):
        return '%s / %s' % (self.schema.namespace, self.dataset.description)

    class Meta:
        ordering = ['id']


class ExperimentParameterSet(models.Model):
    schema = models.ForeignKey(Schema)
    experiment = models.ForeignKey(Experiment)

    def __unicode__(self):
        return '%s / %s' % (self.schema.namespace, self.experiment.title)

    class Meta:
        ordering = ['id']


class ParameterName(models.Model):

    EXACT_VALUE_COMPARISON = 1
    NOT_EQUAL_COMPARISON = 2
    RANGE_COMPARISON = 3
    GREATER_THAN_COMPARISON = 4
    GREATER_THAN_EQUAL_COMPARISON = 5
    LESS_THAN_COMPARISON = 6
    LESS_THAN_EQUAL_COMPARISON = 7
    CONTAINS_COMPARISON = 8
    __COMPARISON_CHOICES = (
        (EXACT_VALUE_COMPARISON, 'Exact value'),
        (CONTAINS_COMPARISON, 'Contains'),
        # TODO: enable this next time if i figure out how to support
        #(NOT_EQUAL_COMPARISON, 'Not equal'),
        (RANGE_COMPARISON, 'Range'),
        (GREATER_THAN_COMPARISON, 'Greater than'),
        (GREATER_THAN_EQUAL_COMPARISON, 'Greater than or equal'),
        (LESS_THAN_COMPARISON, 'Less than'),
        (LESS_THAN_EQUAL_COMPARISON, 'Less than or equal'),
    )

    NUMERIC = 1
    STRING = 2
    URL = 3
    LINK = 4
    FILENAME = 5
    DATETIME = 6

    __TYPE_CHOICES = (
        (NUMERIC, 'NUMERIC'),
        (STRING, 'STRING'),
        (URL, 'URL'),
        (LINK, 'LINK'),
        (FILENAME, 'FILENAME'),
        (DATETIME, 'DATETIME'))

    schema = models.ForeignKey(Schema)
    name = models.CharField(max_length=60)
    full_name = models.CharField(max_length=60)
    units = models.CharField(max_length=60, blank=True)
    data_type = models.IntegerField(choices=__TYPE_CHOICES, default=STRING)
    immutable = models.BooleanField(default=False)
    comparison_type = models.IntegerField(
        choices=__COMPARISON_CHOICES, default=EXACT_VALUE_COMPARISON)
    is_searchable = models.BooleanField(default=False)
    # TODO: we'll need to rethink the way choices for drop down menus are
    #       represented in the DB. doing it this way is just a bit wasteful.
    choices = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=9999, null=True, blank=True)
    objects = ParameterNameManager()

    class Meta:
        unique_together = (('schema', 'name'),)
        ordering = ('order', 'name')

    def __unicode__(self):
        return (self.schema.name or self.schema.namespace) + ": " + self.name

    def natural_key(self):
        return (self.schema.namespace, self.name)

    def isNumeric(self):
        if self.data_type == self.NUMERIC:
            return True
        else:
            return False

    def isString(self):
        if self.data_type == self.STRING:
            return True
        else:
            return False

    def isURL(self):
        if self.data_type == self.URL:
            return True
        else:
            return False

    def isLink(self):
        if self.data_type == self.LINK:
            return True
        else:
            return False

    def isFilename(self):
        if self.data_type == self.FILENAME:
            return True
        else:
            return False

    def isDateTime(self):
        if self.data_type == self.DATETIME:
            return True
        else:
            return False


def _getParameter(parameter):

    if parameter.name.isNumeric():
        value = str(parameter.numerical_value)
        units = parameter.name.units
        if units:
            value += ' %s' % units
        return value

    elif parameter.name.isString():
        if parameter.name.name.endswith('Image'):
            parset = type(parameter.parameterset).__name__
            viewname = ''
            args = []
            if parset == 'DatafileParameterSet':
                dfid = parameter.parameterset.dataset_file.id
                psid = parameter.parameterset.id
                viewname = 'tardis.tardis_portal.views.display_datafile_image'
                args = [dfid, psid, parameter.name]
            elif parset == 'DatasetParameterSet':
                dsid = parameter.parameterset.dataset.id
                psid = parameter.parameterset.id
                viewname = 'tardis.tardis_portal.views.display_dataset_image'
                args = [dsid, psid, parameter.name]
            elif parset == 'ExperimentParameterSet':
                eid = parameter.parameterset.dataset.id
                psid = parameter.parameterset.id
                viewname = 'tardis.tardis_portal.views.'
                'display_experiment_image'
                args = [eid, psid, parameter.name]
            if viewname:
                value = "<img src='%s' />" % reverse(viewname=viewname,
                                                     args=args)
                return mark_safe(value)

        return parameter.string_value

    elif parameter.name.isURL():
        url = parameter.string_value
        value = "<a href='%s'>%s</a>" % (url, url)
        return mark_safe(value)

    elif parameter.name.isLink():
        if parameter.string_value is None:
            return ''
        units = parameter.name.units
        if units:
            url = units + parameter.string_value
        else:
            url = parameter.string_value
        value = "<a href='%s'>%s</a>" % (url, parameter.string_value)
        return mark_safe(value)

    elif parameter.name.isFilename():
        if parameter.name.units.startswith('image') and parameter.string_value:
            parset = type(parameter.parameterset).__name__
            viewname = ''
            if parset == 'DatafileParameterSet':
                viewname = 'tardis.tardis_portal.views.load_datafile_image'
            elif parset == 'DatasetParameterSet':
                viewname = 'tardis.tardis_portal.views.load_dataset_image'
            elif parset == 'ExperimentParameterSet':
                viewname = 'tardis.tardis_portal.views.load_experiment_image'
            if viewname:
                value = "<img src='%s' />" % reverse(viewname=viewname,
                                                     args=[parameter.id])
                return mark_safe(value)
        else:
            return parameter.string_value

    elif parameter.name.isDateTime():
        value = str(parameter.datetime_value)
        return value

    else:
        return None


class DatafileParameter(models.Model):

    parameterset = models.ForeignKey(DatafileParameterSet)
    name = models.ForeignKey(ParameterName)
    string_value = models.TextField(null=True, blank=True)
    numerical_value = models.FloatField(null=True, blank=True)
    datetime_value = models.DateTimeField(null=True, blank=True)
    objects = OracleSafeManager()

    def get(self):
        return _getParameter(self)

    def getExpId(self):
        return self.parameterset.dataset_file.dataset.experiment.id

    def __unicode__(self):
        return 'Datafile Param: %s=%s' % (self.name.name, self.get())

    class Meta:
        ordering = ['name']


class DatasetParameter(models.Model):

    parameterset = models.ForeignKey(DatasetParameterSet)
    name = models.ForeignKey(ParameterName)
    string_value = models.TextField(null=True, blank=True)
    numerical_value = models.FloatField(null=True, blank=True)
    datetime_value = models.DateTimeField(null=True, blank=True)
    objects = OracleSafeManager()

    def get(self):
        return _getParameter(self)

    def getExpId(self):
        return self.parameterset.dataset.experiment.id

    def __unicode__(self):
        return 'Dataset Param: %s=%s' % (self.name.name, self.get())

    class Meta:
        ordering = ['name']


class ExperimentParameter(models.Model):
    parameterset = models.ForeignKey(ExperimentParameterSet)
    name = models.ForeignKey(ParameterName)
    string_value = models.TextField(null=True, blank=True)
    numerical_value = models.FloatField(null=True, blank=True)
    datetime_value = models.DateTimeField(null=True, blank=True)
    objects = OracleSafeManager()

    def get(self):
        return _getParameter(self)

    def getExpId(self):
        return self.parameterset.experiment.id

    def __unicode__(self):
        return 'Experiment Param: %s=%s' % (self.name.name, self.get())

    class Meta:
        ordering = ['name']


@receiver(pre_save, sender=ExperimentParameter)
@receiver(pre_save, sender=DatasetParameter)
@receiver(pre_save, sender=DatafileParameter)
def pre_save_parameter(sender, **kwargs):

    # the object can be accessed via kwargs 'instance' key.
    parameter = kwargs['instance']
    if parameter.name.units.startswith('image') \
            and parameter.name.data_type == ParameterName.FILENAME:
        if parameter.string_value:
            from base64 import b64decode
            from os import mkdir
            from os.path import exists, join
            from uuid import uuid4 as uuid

            exp_id = parameter.getExpId()

            dirname = join(settings.FILE_STORE_PATH, str(exp_id))
            filename = str(uuid())
            filepath = join(dirname, filename)

            b64 = parameter.string_value
            modulo = len(b64) % 4
            if modulo:
                b64 += (4 - modulo) * '='

            if not exists(dirname):
                mkdir(dirname)
            f = open(filepath, 'w')
            try:
                f.write(b64decode(b64))
            except TypeError:
                f.write(b64)
            f.close()
            parameter.string_value = filename
