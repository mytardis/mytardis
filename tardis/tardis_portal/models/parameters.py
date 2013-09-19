from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.utils.timezone import is_aware, is_naive, make_aware, make_naive

from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
from tardis.tardis_portal.managers import OracleSafeManager,\
    ParameterNameManager, SchemaManager

from .experiment import Experiment
from .dataset import Dataset
from .datafile import Dataset_File

import logging
import operator
import pytz

LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)
logger = logging.getLogger(__name__)


class ParameterSetManagerMixin(ParameterSetManager):
    '''for clarity's sake and for future extension this class makes
    ParameterSetManager local to this file.
    At the moment its only function is increasing the line count
    '''
    pass


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
                                max_length=255)
    name = models.CharField(blank=True, null=True, max_length=50)
    type = models.IntegerField( #@ReservedAssignment
        choices=_SCHEMA_TYPES, default=EXPERIMENT)

    # subtype will be used for categorising the type of experiment, dataset
    # or datafile schemas. for example, the type of beamlines are usually used
    # further categorise the experiment, dataset, and datafile schemas. the
    # subtype might then allow for the following values: 'mx', 'ir', 'saxs'
    subtype = models.CharField(blank=True, null=True, max_length=30)
    objects = SchemaManager()
    immutable = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)

    class Meta:
        app_label = 'tardis_portal'

    def natural_key(self):
        return (self.namespace,)

    def _getSchemaTypeName(self, typeNum):
        return dict(self._SCHEMA_TYPES)[typeNum]

    @classmethod
    def getSubTypes(cls):
        return set([schema.subtype for schema in Schema.objects.all() \
            if schema.subtype])

    @classmethod
    def getNamespaces(cls, type_, subtype=None):
        """Return the list of namespaces for equipment, sample, and experiment
        schemas.

        """
        if subtype:
            return [schema.namespace for schema in
                    Schema.objects.filter(type=type_, subtype=subtype)]
        else:
            return [schema.namespace for schema in
                    Schema.objects.filter(type=type_)]

    def __unicode__(self):
        return self._getSchemaTypeName(self.type) + (self.subtype and ' for ' +
            self.subtype.upper() or '') + ': ' + self.namespace

    class UnsupportedType(Exception):

        def __init__(self, msg):
            Exception.__init__(self, msg)


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

    LONGSTRING = 7

    __TYPE_CHOICES = (
        (NUMERIC, 'NUMERIC'),
        (STRING, 'STRING'),
        (URL, 'URL'),
        (LINK, 'LINK'),
        (FILENAME, 'FILENAME'),
        (DATETIME, 'DATETIME'),
        (LONGSTRING, 'LONGSTRING')
        )

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
        app_label = 'tardis_portal'
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

    def isLongString(self):
        return self.data_type == self.LONGSTRING

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

    def getUniqueShortName(self):
        return self.name + '_' + str(self.id)


def _getParameter(parameter):

    if parameter.name.isNumeric():
        value = str(parameter.numerical_value)
        units = parameter.name.units
        if units:
            value += ' %s' % units
        return value

    elif parameter.name.isLongString():
        return parameter.string_value

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
                value = "<a href='%s' target='_blank'><img style='width: 300px;' src='%s' /></a>" % \
                     (reverse(viewname=viewname,
                     args=[parameter.id]),
                     reverse(viewname=viewname,
                     args=[parameter.id]))
                return mark_safe(value)
        else:
            return parameter.string_value

    elif parameter.name.isDateTime():
        value = str(parameter.datetime_value)
        return value

    else:
        return None


class ParameterSet(models.Model, ParameterSetManagerMixin):
    schema = models.ForeignKey(Schema)
    parameter_class = None

    class Meta:
        abstract = True
        app_label = 'tardis_portal'
        ordering = ['id']

    def _init_parameterset_accessors(self):
        self.parameterset = self
        self.namespace = self.schema.namespace
        self.parameters = self.parameter_class.objects.filter(
            parameterset=self.parameterset).order_by('name__full_name')
        self.blank_param = self.parameter_class

    def __init__(self, *args, **kwargs):
        super(ParameterSet, self).__init__(*args, **kwargs)
        if self.pk is not None:  # we have a ParameterSet that's manageable
            self._init_parameterset_accessors()

    def save(self, *args, **kwargs):
        super(ParameterSet, self).save(*args, **kwargs)
        self._init_parameterset_accessors()

    def _get_label(self):
        raise NotImplementedError

    def __unicode__(self):
        labelattribute, default = self._get_label()
        try:
            namespace = operator.attrgetter('schema.namespace')(self)
            label = operator.attrgetter(labelattribute)(self)
            return '%s / %s' % (namespace, label)
        except (AttributeError, ObjectDoesNotExist):
            return 'Uninitialised %sParameterSet' % default

    def _has_any_perm(self, user_obj):
        if not hasattr(self, 'id'):
            return False
        return self.parameter_class

    def _has_view_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_change_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_delete_perm(self, user_obj):
        return self._has_any_perm(user_obj)

class Parameter(models.Model):
    name = models.ForeignKey(ParameterName)
    string_value = models.TextField(null=True, blank=True, db_index=True)
    numerical_value = models.FloatField(null=True, blank=True, db_index=True)
    datetime_value = models.DateTimeField(null=True, blank=True, db_index=True)
    #objects = OracleSafeManager()   # Commented by Sindhu E for natural key support
    parameter_type = 'Abstract'
    
    class Meta:
        abstract = True
        app_label = 'tardis_portal'
        ordering = ['name']

    def get(self):
        return _getParameter(self)

    def __unicode__(self):
        try:
            return '%s Param: %s=%s' % (self.parameter_type,
                                        self.name.name, self.get())
        except:
            return 'Unitialised %sParameter' % self.parameter_type

    def set_value(self, value):
        if self.name.isNumeric():
            self.numerical_value = float(value)
        elif self.name.isDateTime():
            if settings.USE_TZ and is_naive(value):
                value = make_aware(value, LOCAL_TZ)
            elif not settings.USE_TZ and is_aware(value):
                value = make_naive(value, LOCAL_TZ)
            self.datetime_value = value
        else:
            self.string_value = unicode(value)

    def _has_any_perm(self, user_obj):
        if not hasattr(self, 'id'):
            return False
        return self.parameterset

    def _has_view_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_change_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_delete_perm(self, user_obj):
        return self._has_any_perm(user_obj)


class DatafileParameter(Parameter):
    parameterset = models.ForeignKey('DatafileParameterSet')
    parameter_type = 'Datafile'

class DatasetParameterManager(OracleSafeManager):
    """
    Added by Sindhu Emilda for natural key implementation.
    The manager for the tardis_portal's DatasetParameter model.
    """
    def get_by_natural_key(self, namespace, name, description):
        return self.get(name=ParameterName.objects.get_by_natural_key(namespace, name),
                        parameterset=DatasetParameterSet.objects.get_by_natural_key(description),
        )

class DatasetParameter(Parameter):
    parameterset = models.ForeignKey('DatasetParameterSet')
    parameter_type = 'Dataset'

    ''' Added by Sindhu Emilda for natural key implementation '''
    objects = DatasetParameterManager()
    
    def natural_key(self):
        return (self.name.natural_key(),) + self.parameterset.natural_key()
    
    natural_key.dependencies = ['tardis_portal.ParameterName', 'tardis_portal.DatasetParameterSet']

class ExperimentParameterManager(OracleSafeManager):
    """
    Added by Sindhu Emilda for natural key implementation.
    The manager for the tardis_portal's ExperimentParameter model.
    """
    def get_by_natural_key(self, namespace, name, nmspace, title, username):
        return self.get(name=ParameterName.objects.get_by_natural_key(namespace, name),
                        parameterset=ExperimentParameterSet.objects.get_by_natural_key(nmspace, title, username),
        )
        
class ExperimentParameter(Parameter):
    parameterset = models.ForeignKey('ExperimentParameterSet')
    parameter_type = 'Experiment'

    ''' Added by Sindhu Emilda for natural key implementation '''
    objects = ExperimentParameterManager()
    
    def natural_key(self):
        return (self.name.natural_key(),) + self.parameterset.natural_key()
    
    natural_key.dependencies = ['tardis_portal.ParameterName', 'tardis_portal.ExperimentParameterSet']
    
    def save(self, *args, **kwargs):
        super(ExperimentParameter, self).save(*args, **kwargs)
        try:
            from .hooks import publish_public_expt_rifcs
            publish_public_expt_rifcs(self.parameterset.experiment)
        except StandardError:
            logger.exception('')

class DatafileParameterSetManager(OracleSafeManager):
    """
    Added by Sindhu Emilda for natural key implementation.
    The manager for the tardis_portal's DatafileParameterSet model.
    """
    def get_by_natural_key(self, namespace, filename, description):
        return self.get(schema=Schema.objects.get_by_natural_key(namespace),
                        dataset_file=Dataset_File.objects.get_by_natural_key(filename, description),
        )

class DatafileParameterSet(ParameterSet):
    dataset_file = models.ForeignKey(Dataset_File)
    parameter_class = DatafileParameter

    ''' Added by Sindhu Emilda for natural key implementation '''
    objects = DatafileParameterSetManager()
    
    def natural_key(self):
        return self.schema.natural_key() + self.dataset_file.natural_key()
    
    natural_key.dependencies = ['tardis_portal.Schema', 'tardis_portal.Dataset_File']

    def _get_label(self):
        return ('dataset_file.filename', 'Datafile')

class DatasetParameterSetManager(OracleSafeManager):
    """
    Added by Sindhu Emilda for natural key implementation.
    The manager for the tardis_portal's DatasetParameterSet model.
    """
    def get_by_natural_key(self, namespace, description):
        return self.get(schema=Schema.objects.get_by_natural_key(namespace),
                        dataset=Dataset.objects.get_by_natural_key(description),
        )

class DatasetParameterSet(ParameterSet):
    dataset = models.ForeignKey(Dataset)
    parameter_class = DatasetParameter

    ''' Added by Sindhu Emilda for natural key implementation '''
    objects = DatasetParameterSetManager()
    
    def natural_key(self):
        return self.schema.natural_key() + self.dataset.natural_key()
    
    natural_key.dependencies = ['tardis_portal.Schema', 'tardis_portal.Dataset']

    def _get_label(self):
        return ('dataset.description', 'Dataset')

class ExperimentParameterSetManager(OracleSafeManager):
    """
    Added by Sindhu Emilda for natural key implementation.
    The manager for the tardis_portal's ExperimentParameterSet model.
    """
    def get_by_natural_key(self, namespace, title, username):
        return self.get(schema=Schema.objects.get_by_natural_key(namespace),
                        experiment=Experiment.objects.get_by_natural_key(title, username),
        )

class ExperimentParameterSet(ParameterSet):
    experiment = models.ForeignKey(Experiment)
    parameter_class = ExperimentParameter

    ''' Added by Sindhu Emilda for natural key implementation '''
    objects = ExperimentParameterSetManager()
    
    def natural_key(self):
        return self.schema.natural_key() + self.experiment.natural_key()
    
    natural_key.dependencies = ['tardis_portal.Schema', 'tardis_portal.Experiment']

    def _get_label(self):
        return ('experiment.title', 'Experiment')


class FreeTextSearchField(models.Model):

    parameter_name = models.ForeignKey(ParameterName)

    class Meta:
        app_label = 'tardis_portal'

    def __unicode__(self):
        return "Index on %s" % (self.parameter_name)
