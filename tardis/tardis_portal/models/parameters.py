# pylint: disable=model-no-explicit-unicode
import logging
import operator
import json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from django.urls import reverse, resolve, Resolver404
from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.timezone import is_aware, is_naive, make_aware, make_naive

import dateutil.parser
import pytz

from ..ParameterSetManager import ParameterSetManager
from ..managers import OracleSafeManager, ParameterNameManager, SchemaManager

from .experiment import Experiment
from .dataset import Dataset
from .datafile import DataFile
from .storage import StorageBox
from .instrument import Instrument


LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)
logger = logging.getLogger(__name__)


class ParameterSetManagerMixin(ParameterSetManager):
    """for clarity's sake and for future extension this class makes
    ParameterSetManager local to this file.
    At the moment its only function is increasing the line count
    """


class Schema(models.Model):

    EXPERIMENT = 1
    DATASET = 2
    DATAFILE = 3
    NONE = 4
    INSTRUMENT = 5
    PROJECT = 6

    _SCHEMA_TYPES = (
        (EXPERIMENT, "Experiment schema"),
        (DATASET, "Dataset schema"),
        (DATAFILE, "Datafile schema"),
        (NONE, "None"),
        (INSTRUMENT, "Instrument schema"),
        (PROJECT, "Project schema"),
    )

    _SCHEMA_TYPES_SHORT = (
        (EXPERIMENT, "experiment"),
        (DATASET, "dataset"),
        (DATAFILE, "datafile"),
        (NONE, "none"),
        (INSTRUMENT, "instrument"),
        (PROJECT, "project"),
    )

    namespace = models.URLField(unique=True, max_length=255)
    name = models.CharField(blank=True, null=True, max_length=50)
    # WHY 'type', a reserved word? Someone please refactor and migrate db
    type = models.IntegerField(  # @ReservedAssignment
        choices=_SCHEMA_TYPES, default=EXPERIMENT
    )

    # subtype will be used for categorising the type of experiment, dataset
    # or datafile schemas. for example, the type of beamlines are usually used
    # further categorise the experiment, dataset, and datafile schemas. the
    # subtype might then allow for the following values: 'mx', 'ir', 'saxs'
    subtype = models.CharField(blank=True, null=True, max_length=30)
    objects = SchemaManager()
    immutable = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)

    class Meta:
        app_label = "tardis_portal"

    def natural_key(self):
        return (self.namespace,)

    def _getSchemaTypeName(self, typeNum):
        return dict(self._SCHEMA_TYPES)[typeNum]

    def __str__(self):
        return (
            self._getSchemaTypeName(self.type)
            + (self.subtype and " for " + self.subtype.upper() or "")
            + ": "
            + self.namespace
        )

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
        (EXACT_VALUE_COMPARISON, "Exact value"),
        (CONTAINS_COMPARISON, "Contains"),
        # TODO: enable this next time if i figure out how to support
        # (NOT_EQUAL_COMPARISON, 'Not equal'),
        (RANGE_COMPARISON, "Range"),
        (GREATER_THAN_COMPARISON, "Greater than"),
        (GREATER_THAN_EQUAL_COMPARISON, "Greater than or equal"),
        (LESS_THAN_COMPARISON, "Less than"),
        (LESS_THAN_EQUAL_COMPARISON, "Less than or equal"),
    )

    NUMERIC = 1
    STRING = 2
    URL = 3
    LINK = 4
    FILENAME = 5
    DATETIME = 6
    LONGSTRING = 7
    JSON = 8

    __TYPE_CHOICES = (
        (NUMERIC, "NUMERIC"),
        (STRING, "STRING"),
        (URL, "URL"),
        (LINK, "LINK"),
        (FILENAME, "FILENAME"),
        (DATETIME, "DATETIME"),
        (LONGSTRING, "LONGSTRING"),
        (JSON, "JSON"),
    )

    schema = models.ForeignKey(Schema, on_delete=models.CASCADE)
    name = models.CharField(max_length=60)
    full_name = models.CharField(max_length=60)
    units = models.CharField(max_length=60, blank=True)
    data_type = models.IntegerField(choices=__TYPE_CHOICES, default=STRING)
    immutable = models.BooleanField(default=False)
    comparison_type = models.IntegerField(
        choices=__COMPARISON_CHOICES, default=EXACT_VALUE_COMPARISON
    )
    is_searchable = models.BooleanField(default=False)
    # TODO: we'll need to rethink the way choices for drop down menus are
    #       represented in the DB. doing it this way is just a bit wasteful.
    sensitive = models.BooleanField(default=False)
    choices = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=9999, null=True, blank=True)
    objects = ParameterNameManager()

    class Meta:
        app_label = "tardis_portal"
        unique_together = (("schema", "name"),)
        ordering = ("order", "name")

    def __str__(self):
        return (self.schema.name or self.schema.namespace) + ": " + self.name

    def natural_key(self):
        return (self.schema.namespace, self.name)

    def isNumeric(self):
        return self.data_type == self.NUMERIC

    def isLongString(self):
        return self.data_type == self.LONGSTRING

    def isString(self):
        return self.data_type == self.STRING

    def isURL(self):
        return self.data_type == self.URL

    def isLink(self):
        return self.data_type == self.LINK

    def isFilename(self):
        return self.data_type == self.FILENAME

    def isDateTime(self):
        return self.data_type == self.DATETIME

    def getUniqueShortName(self):
        return self.name + "_" + str(self.id)

    def is_json(self):
        return self.data_type == self.JSON


def _get_filename_parameter_as_image_element(parameter):
    """
    Detect if a parameter name contains the prefix 'image' in a parameter set
    associated with an Experiment, Dataset or DataFile.
    If so, return an associated HTML <img> element.

    Associated ParameterName must be of type FILENAME, however the
    string_value is not used.

    :param parameter: The Parameter instance
    :type parameter: tardis.tardis_portal.models.parameters.Parameter
    :return: An HTML formated img element, or None
    :rtype: basestring | types.NoneType
    """
    assert (
        parameter.name.isFilename()
    ), "'image*' parameters are expected to be of type FILENAME"

    if (
        parameter.name.isFilename()
        and parameter.name.units.startswith("image")
        and parameter.string_value
    ):
        parset = type(parameter.parameterset).__name__
        viewname = None
        if parset == "DatafileParameterSet":
            viewname = "tardis.tardis_portal.views.load_datafile_image"
        elif parset == "DatasetParameterSet":
            viewname = "tardis.tardis_portal.views.load_dataset_image"
        elif parset == "ExperimentParameterSet":
            viewname = "tardis.tardis_portal.views.load_experiment_image"
        if viewname is not None:
            value = (
                "<a href='%s' target='_blank'>"
                "<img style='width: 300px;' src='%s' /></a>"
                % (
                    reverse(viewname=viewname, args=[parameter.id]),
                    reverse(viewname=viewname, args=[parameter.id]),
                )
            )
            return mark_safe(value)

    return None


def _get_parameter(parameter):

    if parameter.name.isNumeric():
        value = str(parameter.numerical_value)
        units = parameter.name.units
        if units:
            value += " %s" % units
        return value

    if parameter.name.isLongString() or parameter.name.isString():
        return parameter.string_value

    if parameter.name.isFilename():
        as_img_element = _get_filename_parameter_as_image_element(parameter)

        return as_img_element if as_img_element is not None else parameter.string_value

    if parameter.name.isURL():
        url = parameter.string_value
        value = "<a href='%s'>%s</a>" % (url, url)
        return mark_safe(value)

    if parameter.name.isLink():
        if parameter.string_value is None:
            return ""
        units = parameter.name.units
        if units:
            url = units + parameter.string_value
        else:
            url = parameter.string_value
        value = "<a href='%s'>%s</a>" % (url, parameter.string_value)
        return mark_safe(value)

    if parameter.name.isDateTime():
        try:
            value = parameter.datetime_value.astimezone(tz=LOCAL_TZ).strftime("%c")
        except ValueError:
            value = parameter.datetime_value.strftime("%c")
        return value

    if parameter.name.is_json():
        return json.loads(parameter.string_value)

    return None


class ParameterSet(models.Model, ParameterSetManagerMixin):
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE)
    storage_box = models.ManyToManyField(StorageBox, related_name="%(class)ss")
    parameter_class = None

    class Meta:
        abstract = True
        app_label = "tardis_portal"
        ordering = ["id"]

    def _init_parameterset_accessors(self):
        self.parameterset = self
        self.namespace = self.schema.namespace
        self.parameters = self.parameter_class.objects.filter(
            parameterset=self.parameterset
        ).order_by("name__full_name")
        self.blank_param = self.parameter_class

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pk is not None:  # we have a ParameterSet that's manageable
            self._init_parameterset_accessors()

    # pylint: disable=W0222
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._init_parameterset_accessors()

    def _get_label(self):
        raise NotImplementedError

    def __str__(self):
        labelattribute, default = self._get_label()
        try:
            namespace = operator.attrgetter("schema.namespace")(self)
            label = operator.attrgetter(labelattribute)(self)
            return "%s / %s" % (namespace, label)
        except (AttributeError, ObjectDoesNotExist):
            return "Uninitialised %sParameterSet" % default

    def _has_any_perm(self, user_obj):
        if not hasattr(self, "id"):
            return False
        return self.parameter_class

    def _has_view_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_change_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_delete_perm(self, user_obj):
        return self._has_any_perm(user_obj)


class Parameter(models.Model):
    name = models.ForeignKey(ParameterName, on_delete=models.CASCADE)
    # string_value has a custom index created via migrations (for Postgresql)
    string_value = models.TextField(null=True, blank=True)
    numerical_value = models.FloatField(null=True, blank=True, db_index=True)
    datetime_value = models.DateTimeField(null=True, blank=True, db_index=True)
    link_id = models.PositiveIntegerField(null=True, blank=True)
    link_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.CASCADE
    )
    link_gfk = GenericForeignKey("link_ct", "link_id")
    objects = OracleSafeManager()
    parameter_type = "Abstract"

    class Meta:
        abstract = True
        app_label = "tardis_portal"
        ordering = ["name"]

    def get(self):
        return _get_parameter(self)

    def __str__(self):
        try:
            return "%s Param: %s=%s" % (self.parameter_type, self.name.name, self.get())
        except:
            return "Unitialised %sParameter" % self.parameter_type

    @property
    def link_url(self):
        if not self.name.isLink():
            return None
        if isinstance(self.link_gfk, DataFile):
            url = reverse(
                "tardis_portal.view_dataset",
                kwargs={"dataset_id": self.link_gfk.dataset.id},
            )
        elif isinstance(self.link_gfk, Dataset):
            url = reverse(
                "tardis_portal.view_dataset", kwargs={"dataset_id": self.link_id}
            )
        elif isinstance(self.link_gfk, Experiment):
            url = reverse(
                "tardis_portal.view_experiment", kwargs={"experiment_id": self.link_id}
            )
        elif self.link_gfk is None and self.string_value:
            url = self.string_value
        else:
            raise NotImplementedError
        return url

    def set_value(self, value):
        """
        Sets the parameter value, converting into the appropriate data type.
        Deals with date/time strings that are timezone naive or aware, based
        on the USE_TZ setting.

        :param basestring value: a string (or string-like) repr of the value
        :raises SuspiciousOperation:
        """
        if self.name.isNumeric():
            self.numerical_value = float(value)
        elif self.name.isDateTime():
            # We convert the value string into datetime object.
            # dateutil.parser detects and converts many date formats and is
            # quite permissive in what it accepts (form validation and API
            # input validation happens elsewhere and may be less permissive)
            datevalue = dateutil.parser.parse(value)
            if settings.USE_TZ and is_naive(datevalue):
                datevalue = make_aware(datevalue, LOCAL_TZ, settings.IS_DST)
            elif not settings.USE_TZ and is_aware(datevalue):
                datevalue = make_naive(datevalue, LOCAL_TZ)
            self.datetime_value = datevalue
        elif self.name.isLink():
            # Always store the raw value as a string, even if setting
            # the GenericForeignKey via link_id/link_ct
            if str(value) == "" or value is None:
                return
            self.string_value = str(value)

            try:
                # We detect experiment or dataset view URLs
                # (eg, /experiment/view/12345/ or /api/v1/dataset/456)
                # and extract values to populate link_ct and link_id. This
                # covers two common cases, allowing LINK Parameters to be
                # properly created via the REST API.

                match = resolve(value)
                if match.view_name == u"api_dispatch_detail":
                    model_name = match.kwargs.get(u"resource_name", None)
                    if model_name not in ("experiment", "dataset"):
                        model_name, pk = None, None
                    else:
                        pk = match.kwargs.get("pk", None)
                elif match.view_name.endswith("view_experiment"):
                    model_name = "experiment"
                    pk = match.kwargs.get("experiment_id")
                elif match.view_name.endswith("view_dataset"):
                    model_name = "dataset"
                    pk = match.kwargs.get("dataset_id")
                else:
                    model_name, pk = None, None

                if pk is not None and model_name is not None:
                    self.link_id = pk
                    self.link_ct = ContentType.objects.get(
                        app_label="tardis_portal", model=model_name.lower()
                    )
            except (ValueError, IndexError, Resolver404):
                # If we were unable to successfully match the url to model
                # instance, return an error. For any URL the URL Parameter
                # type should be used.
                raise SuspiciousOperation(
                    "Link parameter could not be set " "from string: %s" % str(value)
                )
        else:
            self.string_value = str(value)

    def _has_any_perm(self, user_obj):
        if not hasattr(self, "id"):
            return False
        return self.parameterset

    def _has_view_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_change_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_delete_perm(self, user_obj):
        return self._has_any_perm(user_obj)


class DatafileParameter(Parameter):
    parameterset = models.ForeignKey("DatafileParameterSet", on_delete=models.CASCADE)
    parameter_type = "Datafile"


class DatasetParameter(Parameter):
    parameterset = models.ForeignKey("DatasetParameterSet", on_delete=models.CASCADE)
    parameter_type = "Dataset"


class ExperimentParameter(Parameter):
    parameterset = models.ForeignKey("ExperimentParameterSet", on_delete=models.CASCADE)
    parameter_type = "Experiment"

    # pylint: disable=W0222
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            from .hooks import publish_public_expt_rifcs

            publish_public_expt_rifcs(self.parameterset.experiment)
        except Exception:
            logger.exception("")


class InstrumentParameter(Parameter):
    parameterset = models.ForeignKey("InstrumentParameterSet", on_delete=models.CASCADE)
    parameter_type = "Instrument"


class DatafileParameterSet(ParameterSet):
    datafile = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    parameter_class = DatafileParameter

    def _get_label(self):
        return ("datafile.filename", "Datafile")


class DatasetParameterSet(ParameterSet):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    parameter_class = DatasetParameter

    def _get_label(self):
        return ("dataset.description", "Dataset")


class InstrumentParameterSet(ParameterSet):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    parameter_class = InstrumentParameter

    def _get_label(self):
        return ("instrument.name", "Instrument")


class ExperimentParameterSet(ParameterSet):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    parameter_class = ExperimentParameter

    def _get_label(self):
        return ("experiment.title", "Experiment")


class FreeTextSearchField(models.Model):

    parameter_name = models.ForeignKey(ParameterName, on_delete=models.CASCADE)

    class Meta:
        app_label = "tardis_portal"

    def __str__(self):
        return "Index on %s" % (self.parameter_name)
