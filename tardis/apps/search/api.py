"""
RESTful API for MyTardis search.
Implemented with Tastypie.

.. moduleauthor:: Manish Kumar <rishimanish123@gmail.com>
.. moduleauthor:: Mike Laverick <mike.laverick@auckland.ac.nz>
"""
import json
import datetime
from datetime import datetime
import pytz

from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django_elasticsearch_dsl.search import Search
from elasticsearch_dsl import MultiSearch, Q
from tastypie import fields
from tastypie.resources import Resource, Bundle
from tastypie.serializers import Serializer
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpUnauthorized

from tardis.tardis_portal.api import default_authentication
from tardis.tardis_portal.models import (
    Experiment,
    Dataset,
    DataFile,
    Schema,
    ParameterName,
)
from tardis.apps.projects.models import Project


LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)
RESULTS_PER_PAGE = settings.RESULTS_PER_PAGE
MIN_CUTOFF_SCORE = settings.MIN_CUTOFF_SCORE


class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return (
            json.dumps(
                data,
                cls=json.JSONEncoder,
                sort_keys=True,
                ensure_ascii=False,
                indent=self.json_indent,
            )
            + "\n"
        )


if settings.DEBUG:
    default_serializer = PrettyJSONSerializer()
else:
    default_serializer = Serializer()


class SearchObject(object):
    def __init__(self, hits=None, total_hits=None, id=None):
        self.hits = hits
        self.total_hits = total_hits
        self.id = id


class SchemasObject(object):
    def __init__(self, schemas=None, id=None):
        self.schemas = schemas
        self.id = id


class SchemasAppResource(Resource):
    """Tastypie resource for schemas"""

    schemas = fields.ApiField(attribute="schemas", null=True)

    class Meta:
        resource_name = "get-schemas"
        list_allowed_methods = ["get"]
        serializer = default_serializer
        authentication = default_authentication
        object_class = SchemasObject
        always_return_data = True

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs["pk"] = bundle_or_obj.obj.id
        else:
            kwargs["pk"] = bundle_or_obj["id"]

        return kwargs

    def get_object_list(self, request):
        if not request.user.is_authenticated:
            result_dict = {
                "project": None,
                "experiment": None,
                "dataset": None,
                "datafile": None,
            }
            return [SchemasObject(id=1, schemas=result_dict)]
        result_dict = {
            "project": [
                *{
                    *Project.safe.all(request.user)
                    .prefetch_related("projectparameterset")
                    .values_list("projectparameterset__schema__id", flat=True)
                }
            ],
            "experiment": [
                *{
                    *Experiment.safe.all(request.user)
                    .prefetch_related("experimentparameterset")
                    .values_list("experimentparameterset__schema__id", flat=True)
                }
            ],
            "dataset": [
                *{
                    *Dataset.safe.all(request.user)
                    .prefetch_related("datasetparameterset")
                    .values_list("datasetparameterset__schema__id", flat=True)
                }
            ],
            "datafile": [
                *{
                    *DataFile.safe.all(request.user)
                    .prefetch_related("datafileparameterset")
                    .values_list("datafileparameterset__schema__id", flat=True)
                }
            ],
        }
        safe_dict = {}
        for key in result_dict:
            safe_dict[key] = {}
            for value in result_dict[key]:
                if value is not None:
                    schema_id = str(value)
                    schema_dict = {
                        "id": schema_id,
                        "type": key,
                        "schema_name": Schema.objects.get(id=value).name,
                        "parameters": {},
                    }
                    param_names = ParameterName.objects.filter(schema__id=value)
                    for param in param_names:
                        type_dict = {
                            1: "NUMERIC",
                            2: "STRING",
                            3: "URL",
                            4: "LINK",
                            5: "FILENAME",
                            6: "DATETIME",
                            7: "LONGSTRING",
                            8: "JSON",
                        }
                        param_id = str(param.id)
                        param_dict = {
                            "id": param_id,
                            "full_name": param.full_name,
                            "data_type": type_dict[param.data_type],
                        }
                        schema_dict["parameters"][param_id] = param_dict
                    safe_dict[key][schema_id] = schema_dict

        return [SchemasObject(id=1, schemas=safe_dict)]

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


class SearchAppResource(Resource):
    """Tastypie resource for simple-search"""

    hits = fields.ApiField(attribute="hits", null=True)

    class Meta:
        resource_name = "simple-search"
        list_allowed_methods = ["get"]
        serializer = default_serializer
        authentication = default_authentication
        object_class = SearchObject
        always_return_data = True

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs["pk"] = bundle_or_obj.obj.id
        else:
            kwargs["pk"] = bundle_or_obj["id"]

        return kwargs

    def log_search_event(self, request, query_text, result_dict):
        # Log search event
        if getattr(settings, "ENABLE_EVENTLOG", False):
            from tardis.apps.eventlog.utils import log

            log(
                action="SEARCH",
                extra={
                    "query": query_text,
                    "experiments": len(result_dict["experiments"]),
                    "datasets": len(result_dict["datasets"]),
                    "datafiles": len(result_dict["datafiles"]),
                },
                request=request,
            )

    def get_object_list(self, request):
        user = request.user
        query_text = request.GET.get("query", None)
        if not user.is_authenticated:
            result_dict = simple_search_public_data(query_text)
            self.log_search_event(request, query_text, result_dict)
            return [SearchObject(id=1, hits=result_dict)]
        groups = user.groups.all()
        index_list = ["experiments", "dataset", "datafile"]
        ms = MultiSearch(index=index_list)

        query_exp = Q("match", title=query_text)
        query_exp_oacl = Q("term", acls__entityId=user.id) | Q(
            "term", public_access=100
        )
        for group in groups:
            query_exp_oacl = query_exp_oacl | Q("term", acls__entityId=group.id)
        query_exp = query_exp & query_exp_oacl
        ms = ms.add(
            Search(index="experiments")
            .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
            .query(query_exp)
        )

        query_dataset = Q("match", description=query_text)

        query_dataset_oacl = Q("term", acls__entityId=user.id) | Q(
            "term", public_access=100
        )
        for group in groups:
            query_dataset_oacl = query_dataset_oacl | Q("term", acls__entityId=group.id)
        query_dataset = query_dataset & query_dataset_oacl
        ms = ms.add(
            Search(index="dataset")
            .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
            .query(query_dataset)
        )

        query_datafile = Q("match", filename=query_text)
        query_datafile_oacl = Q("term", acls__entityId=user.id) | Q(
            "term", public_access=100
        )
        for group in groups:
            query_datafile_oacl = query_datafile_oacl | Q(
                "term", acls__entityId=group.id
            )
        query_datafile = query_datafile & query_datafile_oacl
        ms = ms.add(
            Search(index="datafile")
            .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
            .query(query_datafile)
        )
        results = ms.execute()
        result_dict = {k: [] for k in ["experiments", "datasets", "datafiles"]}
        for item in results:
            for hit in item.hits.hits:
                if hit["_index"] == "dataset":
                    result_dict["datasets"].append(hit.to_dict())

                elif hit["_index"] == "experiments":
                    result_dict["experiments"].append(hit.to_dict())

                elif hit["_index"] == "datafile":
                    result_dict["datafiles"].append(hit.to_dict())
        self.log_search_event(request, query_text, result_dict)
        return [SearchObject(id=1, hits=result_dict)]

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


def simple_search_public_data(query_text):
    result_dict = {k: [] for k in ["experiments", "datasets", "datafiles"]}
    index_list = ["experiments", "dataset", "datafile"]
    ms = MultiSearch(index=index_list)
    query_exp = Q("match", title=query_text)
    query_exp_oacl = Q("term", public_access=100)
    query_exp = query_exp & query_exp_oacl
    ms = ms.add(
        Search(index="experiments")
        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
        .query(query_exp)
    )
    query_dataset = Q("match", description=query_text)
    query_dataset_oacl = Q("term", public_access=100)
    query_dataset = query_dataset & query_dataset_oacl
    ms = ms.add(
        Search(index="dataset")
        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
        .query(query_dataset)
    )
    query_datafile = Q("match", filename=query_text)
    query_datafile_oacl = Q("term", public_access=100)
    query_datafile = query_datafile & query_datafile_oacl
    ms = ms.add(
        Search(index="datafile")
        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
        .query(query_datafile)
    )
    results = ms.execute()
    for item in results:
        for hit in item.hits.hits:
            if hit["_index"] == "dataset":
                result_dict["datasets"].append(hit.to_dict())

            elif hit["_index"] == "experiments":
                result_dict["experiments"].append(hit.to_dict())

            elif hit["_index"] == "datafile":
                result_dict["datafiles"].append(hit.to_dict())
    return result_dict


class AdvanceSearchAppResource(Resource):
    hits = fields.ApiField(attribute="hits", null=True)

    class Meta:
        resource_name = "advance-search"
        list_allowed_methods = ["post"]
        serializer = default_serializer
        authentication = default_authentication
        object_class = SearchObject
        always_return_data = True

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs["pk"] = bundle_or_obj.obj.id
        else:
            kwargs["pk"] = bundle_or_obj["id"]

        return kwargs

    def get_object_list(self, request):
        return request

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_create(self, bundle, **kwargs):
        user = bundle.request.user
        groups = user.groups.all()

        # if anonymous user search public data only
        query_text = bundle.data.get("text", None)
        type_tag = bundle.data.get("TypeTag", [])
        index_list = []
        for type in type_tag:
            if type == "Experiment":
                index_list.append("experiments")
            elif type == "Dataset":
                index_list.append("dataset")
            elif type == "Datafile":
                index_list.append("datafile")
        end_date = bundle.data.get("EndDate", None)
        start_date = bundle.data.get("StartDate", None)
        if end_date is not None:
            end_date_utc = datetime.datetime.strptime(
                end_date, "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=pytz.timezone("UTC"))
            end_date = end_date_utc.astimezone(LOCAL_TZ).date()
        else:
            # set end date to today's date
            end_date = datetime.datetime.today().replace(tzinfo=pytz.timezone("UTC"))
        if start_date:
            start_date_utc = datetime.datetime.strptime(
                start_date, "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=pytz.timezone("UTC"))
            start_date = start_date_utc.astimezone(LOCAL_TZ).date()
        instrument_list = bundle.data.get("InstrumentList", None)
        instrument_list_id = []
        if instrument_list:
            for ins in instrument_list:
                instrument_list_id.append(Instrument.objects.get(name__exact=ins).id)
        # query for experiment model
        ms = MultiSearch(index=index_list)
        if "experiments" in index_list:
            query_exp = Q("match", title=query_text)
            if user.is_authenticated:
                query_exp_oacl = Q("term", acls__entityId=user.id) | Q(
                    "term", public_access=100
                )
                for group in groups:
                    query_exp_oacl = query_exp_oacl | Q("term", acls__entityId=group.id)
            else:
                query_exp_oacl = Q("term", public_access=100)
            if start_date is not None:
                query_exp = query_exp & Q(
                    "range", created_time={"gte": start_date, "lte": end_date}
                )
            query_exp = query_exp & query_exp_oacl
            ms = ms.add(
                Search(index="experiments")
                .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                .query(query_exp)
            )
        if "dataset" in index_list:
            query_dataset = Q("match", description=query_text)
            if user.is_authenticated:
                query_dataset_oacl = Q("term", acls__entityId=user.id) | Q(
                    "term", public_access=100
                )
                for group in groups:
                    query_dataset_oacl = query_dataset_oacl | Q(
                        "term", **{"acls.entityId": group.id}
                    )
            else:
                query_dataset_oacl = Q("term", **{"public_access": 100})
            if start_date is not None:
                query_dataset = query_dataset & Q(
                    "range", created_time={"gte": start_date, "lte": end_date}
                )
            if instrument_list:
                query_dataset = query_dataset & Q(
                    "terms", **{"instrument.id": instrument_list_id}
                )
            # add instrument query
            query_dataset = query_dataset & query_dataset_oacl
            ms = ms.add(
                Search(index="dataset")
                .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                .query(query_dataset)
            )
        if "datafile" in index_list:
            query_datafile = Q("match", filename=query_text)
            if user.is_authenticated:
                query_datafile_oacl = Q("term", acls__entityId=user.id) | Q(
                    "term", public_access=100
                )
                for group in groups:
                    query_datafile_oacl = query_datafile_oacl | Q(
                        "term", acls__entityId=group.id
                    )
            else:
                query_datafile_oacl = Q("term", public_access=100)
            if start_date is not None:
                query_datafile = query_datafile & Q(
                    "range", created_time={"gte": start_date, "lte": end_date}
                )
            query_datafile = query_datafile & query_datafile_oacl
            ms = ms.add(
                Search(index="datafile")
                .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                .query(query_datafile)
            )
        result = ms.execute()
        result_dict = {k: [] for k in ["experiments", "datasets", "datafiles"]}
        for item in result:
            for hit in item.hits.hits:
                if hit["_index"] == "dataset":
                    result_dict["datasets"].append(hit.to_dict())

                elif hit["_index"] == "experiments":
                    result_dict["experiments"].append(hit.to_dict())

                elif hit["_index"] == "datafile":
                    result_dict["datafiles"].append(hit.to_dict())

        if bundle.request.method == "POST":
            bundle.obj = SearchObject(id=1, hits=result_dict)
        return bundle
