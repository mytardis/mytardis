# pylint: disable=C0302,R1702
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
from tardis.tardis_portal.auth import decorators as authz
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

parname_type_dict = {
    1: "NUMERIC",
    2: "STRING",
    3: "URL",
    4: "LINK",
    5: "FILENAME",
    6: "DATETIME",
    7: "LONGSTRING",
    8: "JSON",
}


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
                    .values_list(
                        "projectparameterset__schema__id",
                        "projectparameterset__schema__name",
                        "id",
                    )
                }
            ],
            "experiment": [
                *{
                    *Experiment.safe.all(request.user)
                    .prefetch_related("experimentparameterset")
                    .values_list(
                        "experimentparameterset__schema__id",
                        "experimentparameterset__schema__name",
                        "id",
                    )
                }
            ],
            "dataset": [
                *{
                    *Dataset.safe.all(request.user)
                    .prefetch_related("datasetparameterset")
                    .values_list(
                        "datasetparameterset__schema__id",
                        "datasetparameterset__schema__name",
                        "id",
                    )
                }
            ],
            "datafile": [
                *{
                    *DataFile.safe.all(request.user)
                    .prefetch_related("datafileparameterset")
                    .values_list(
                        "datafileparameterset__schema__id",
                        "datafileparameterset__schema__name",
                        "id",
                    )
                }
            ],
        }
        safe_dict = {}
        for key in result_dict:
            safe_dict[key] = {}
            for values in result_dict[key]:
                if values is not None:
                    schema_id = str(values[0])
                    schema_dict = {
                        "id": schema_id,
                        "type": key,
                        "schema_name": values[1],
                        "parameters": {},
                        "complete": False,
                    }
                    if not schema_id in safe_dict[key]:
                        safe_dict[key][schema_id] = schema_dict
                    elif safe_dict[key][schema_id]["complete"]:
                        continue
                    param_names = [
                        *ParameterName.objects.filter(schema__id=values[0]).values_list(
                            "id", "full_name", "data_type", "sensitive"
                        )
                    ]
                    if len(param_names) > len(safe_dict[key][schema_id]["parameters"]):
                        for pn in param_names:
                            if (
                                str(pn[0])
                                not in safe_dict[key][schema_id]["parameters"]
                            ):
                                param_dict = {
                                    "id": str(pn[0]),
                                    "full_name": pn[1],
                                    "data_type": parname_type_dict[pn[2]],
                                }
                            if pn[3] and not authz.has_sensitive_access(
                                request.user, values[2], key
                            ):
                                continue
                            safe_dict[key][schema_id]["parameters"][
                                str(pn[0])
                            ] = param_dict
                    if len(param_names) == len(safe_dict[key][schema_id]["parameters"]):
                        safe_dict[key][schema_id]["complete"] = True
            for values in safe_dict[key].values():
                values.pop("complete")
        # pop completed key
        return [SchemasObject(id=1, schemas=safe_dict)]

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


class SearchAppResource(Resource):
    """Tastypie resource for search"""

    hits = fields.ApiField(attribute="hits", null=True)
    total_hits = fields.ApiField(attribute="total_hits", null=True)

    class Meta:
        resource_name = "search"
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
        bundle = self.create_search_results(bundle)
        return bundle

    def create_search_results(self, bundle):
        user = bundle.request.user
        if not user.is_authenticated:
            # Return a 401 error to ask users to log in.
            raise ImmediateHttpResponse(
                response=HttpUnauthorized(
                    "Search not yet available for public use; Please log in."
                )
            )
            # result_dict = simple_search_public_data(query_text)
            # return [SearchObject(id=1, hits=result_dict)]
        groups = user.groups.all()

        query_text = bundle.data.get("query", None)
        filters = bundle.data.get("filters", None)
        request_sorting = bundle.data.get("sort", None)
        request_size = bundle.data.get("size", 20)
        request_offset = bundle.data.get("offset", 0)
        request_type = bundle.data.get("type", None)
        # Mock input
        # request_for_pag = True
        # if request_for_pag:
        #    request_offset = 37
        #    request_size = 50
        #    request_sorting = [#{ 'field': ["title"], 'order': "desc" },
        #                       #{ 'field': ["experiments","title"], 'order': "desc" },
        #                       { 'field': ["size"], 'order': "desc" }]
        #    request_type = 'datafile'
        if request_type is None:
            index_list = ["project", "experiment", "dataset", "datafile"]
            match_list = ["name", "title", "description", "filename"]
        else:
            # probably some nicer structure/way to do this
            type_2_list = {
                "project": {"index": ["project"], "match": ["name"]},
                "experiment": {
                    "index": ["project", "experiment"],
                    "match": ["name", "title"],
                },
                "dataset": {
                    "index": ["project", "experiment", "dataset"],
                    "match": ["name", "title", "description"],
                },
                "datafile": {
                    "index": ["project", "experiment", "dataset", "datafile"],
                    "match": ["name", "title", "description", "filename"],
                },
            }
            index_list = type_2_list[request_type]["index"]
            match_list = type_2_list[request_type]["match"]

        hierarchy = {"project": 4, "experiment": 3, "dataset": 2, "datafile": 1}
        filter_level = 0
        ms = MultiSearch(index=index_list)
        for idx, obj in enumerate(index_list):

            # (1) add user/group criteria to searchers
            query_obj = Q(
                {
                    "nested": {
                        "path": "acls",
                        "query": Q(
                            {
                                "bool": {
                                    "must": [
                                        Q({"match": {"acls.entityId": user.id}}),
                                        Q({"term": {"acls.pluginId": "django_user"}}),
                                    ]
                                }
                            }
                        ),
                    }
                }
            )
            for group in groups:
                query_obj_group = Q(
                    {
                        "nested": {
                            "path": "acls",
                            "query": Q(
                                {
                                    "bool": {
                                        "must": [
                                            Q({"match": {"acls.entityId": group.id}}),
                                            Q(
                                                {
                                                    "term": {
                                                        "acls.pluginId": "django_group"
                                                    }
                                                }
                                            ),
                                        ]
                                    }
                                }
                            ),
                        }
                    }
                )
                query_obj = query_obj | query_obj_group

            # (2) Search on title/keywords + on non-sensitive metadata
            if query_text is not None:
                if filter_level < hierarchy[obj]:
                    filter_level = hierarchy[obj]
                if obj in query_text.keys():
                    query_obj_text = Q({"match": {match_list[idx]: query_text[obj]}})
                    query_obj_text_meta = Q(
                        {
                            "nested": {
                                "path": "parameters.string",
                                "query": Q(
                                    {
                                        "bool": {
                                            "must": [
                                                Q(
                                                    {
                                                        "match": {
                                                            "parameters.string.value": query_text[
                                                                obj
                                                            ]
                                                        }
                                                    }
                                                ),
                                                Q(
                                                    {
                                                        "term": {
                                                            "parameters.string.sensitive": False
                                                        }
                                                    }
                                                ),
                                            ]
                                        }
                                    }
                                ),
                            }
                        }
                    )
                    query_obj_text_meta = query_obj_text | query_obj_text_meta
                    query_obj = query_obj & query_obj_text_meta

            # (3) Apply intrinsic filters + metadata filters to search
            if filters is not None:
                # filter_op = filters['op']     This isn't used for now
                filterlist = filters["content"]
                operator_dict = {
                    "is": "term",
                    "contains": "match",
                    ">=": "gte",
                    "<=": "lte",
                }
                num_2_type = {
                    1: "experiment",
                    2: "dataset",
                    3: "datafile",
                    6: "project",
                }
                for filter in filterlist:
                    oper = operator_dict[filter["op"]]

                    # (3.1) Apply Schema-parameter / metadata filters to search
                    if filter["kind"] == "schemaParameter":
                        schema_id, param_id = filter["target"][0], filter["target"][1]
                        # check filter is applied to correct object type
                        if num_2_type[Schema.objects.get(id=schema_id).type] == obj:
                            if filter_level < hierarchy[obj]:
                                filter_level = hierarchy[obj]
                            if filter["type"] == "STRING":
                                # check if filter query is list of options, or single value
                                # (elasticsearch can actually handle delimiters in a single string...)
                                if isinstance(filter["content"], list):
                                    Qdict = {"should": []}
                                    for option in filter["content"]:
                                        qry = Q(
                                            {
                                                "nested": {
                                                    "path": "parameters.string",
                                                    "query": Q(
                                                        {
                                                            "bool": {
                                                                "must": [
                                                                    Q(
                                                                        {
                                                                            "match": {
                                                                                "parameters.string.pn_id": str(
                                                                                    param_id
                                                                                )
                                                                            }
                                                                        }
                                                                    ),
                                                                    Q(
                                                                        {
                                                                            oper: {
                                                                                "parameters.string.value": option
                                                                            }
                                                                        }
                                                                    ),
                                                                ]
                                                            }
                                                        }
                                                    ),
                                                }
                                            }
                                        )
                                        Qdict["should"].append(qry)
                                    query_obj_filt = Q({"bool": Qdict})
                                else:
                                    query_obj_filt = Q(
                                        {
                                            "nested": {
                                                "path": "parameters.string",
                                                "query": Q(
                                                    {
                                                        "bool": {
                                                            "must": [
                                                                Q(
                                                                    {
                                                                        "match": {
                                                                            "parameters.string.pn_id": str(
                                                                                param_id
                                                                            )
                                                                        }
                                                                    }
                                                                ),
                                                                Q(
                                                                    {
                                                                        oper: {
                                                                            "parameters.string.value": filter[
                                                                                "content"
                                                                            ]
                                                                        }
                                                                    }
                                                                ),
                                                            ]
                                                        }
                                                    }
                                                ),
                                            }
                                        }
                                    )
                            elif filter["type"] == "NUMERIC":
                                query_obj_filt = Q(
                                    {
                                        "nested": {
                                            "path": "parameters.numerical",
                                            "query": Q(
                                                {
                                                    "bool": {
                                                        "must": [
                                                            Q(
                                                                {
                                                                    "match": {
                                                                        "parameters.numerical.pn_id": str(
                                                                            param_id
                                                                        )
                                                                    }
                                                                }
                                                            ),
                                                            Q(
                                                                {
                                                                    "range": {
                                                                        "parameters.numerical.value": {
                                                                            oper: filter[
                                                                                "content"
                                                                            ]
                                                                        }
                                                                    }
                                                                }
                                                            ),
                                                        ]
                                                    }
                                                }
                                            ),
                                        }
                                    }
                                )
                            elif filter["type"] == "DATETIME":
                                query_obj_filt = Q(
                                    {
                                        "nested": {
                                            "path": "parameters.datetime",
                                            "query": Q(
                                                {
                                                    "bool": {
                                                        "must": [
                                                            Q(
                                                                {
                                                                    "match": {
                                                                        "parameters.datetime.pn_id": str(
                                                                            param_id
                                                                        )
                                                                    }
                                                                }
                                                            ),
                                                            Q(
                                                                {
                                                                    "range": {
                                                                        "parameters.datetime.value": {
                                                                            oper: filter[
                                                                                "content"
                                                                            ]
                                                                        }
                                                                    }
                                                                }
                                                            ),
                                                        ]
                                                    }
                                                }
                                            ),
                                        }
                                    }
                                )
                            query_obj = query_obj & query_obj_filt

                    # (3.2) Apply intrinsic object filters to search
                    if filter["kind"] == "typeAttribute":
                        target_objtype, target_fieldtype = (
                            filter["target"][0],
                            filter["target"][1],
                        )
                        if target_objtype == obj:

                            # Update the heirarchy level at which the
                            # "parent-in-results" criteria must be applied
                            if filter_level < hierarchy[obj]:
                                filter_level = hierarchy[obj]

                            # (3.2.1) Apply "Selected Schema" filter
                            if target_fieldtype == "schema":
                                # check if filter query is list of options, or single value
                                if isinstance(filter["content"], list):
                                    Qdict = {"should": []}
                                    for option in filter["content"]:
                                        qry = Q(
                                            {
                                                "nested": {
                                                    "path": "parameters.schemas",
                                                    "query": Q(
                                                        {
                                                            oper: {
                                                                "parameters.schemas.schema_id": option
                                                            }
                                                        }
                                                    ),
                                                }
                                            }
                                        )
                                        Qdict["should"].append(qry)
                                    query_obj_filt = Q({"bool": Qdict})
                                else:
                                    query_obj_filt = Q(
                                        {
                                            "nested": {
                                                "path": "parameters.schemas",
                                                "query": Q(
                                                    {
                                                        oper: {
                                                            "parameters.schemas.schema_id": filter[
                                                                "content"
                                                            ]
                                                        }
                                                    }
                                                ),
                                            }
                                        }
                                    )
                                query_obj = query_obj & query_obj_filt

                            # (3.2.2) Apply filters that act on fields which are
                            # intrinsic to the object (Proj,exp,set,file)
                            if target_fieldtype in {
                                "name",
                                "description",
                                "title",
                                "tags",
                                "filename",
                                "file_extension",
                                "created_time",
                                "start_time",
                                "end_time",
                            }:
                                if filter["type"] == "STRING":
                                    if isinstance(filter["content"], list):
                                        Qdict = {"should": []}
                                        for option in filter["content"]:
                                            if target_fieldtype == "file_extension":
                                                if option[0] == ".":
                                                    option = option[1:]
                                            qry = Q({oper: {target_fieldtype: option}})
                                            Qdict["should"].append(qry)
                                        query_obj_filt = Q({"bool": Qdict})
                                    else:
                                        if target_fieldtype == "file_extension":
                                            if filter["content"][0] == ".":
                                                filter["content"] = filter["content"][
                                                    1:
                                                ]
                                        query_obj_filt = Q(
                                            {
                                                oper: {
                                                    target_fieldtype: filter["content"]
                                                }
                                            }
                                        )
                                elif filter["type"] == "DATETIME":
                                    query_obj_filt = Q(
                                        {
                                            "range": {
                                                target_fieldtype: {
                                                    oper: filter["content"]
                                                }
                                            }
                                        }
                                    )
                                query_obj = query_obj & query_obj_filt

                            # (3.2.3) Apply filters that act on fields which are
                            # intrinsic to related objects (instruments, users, etc)
                            if target_fieldtype in {
                                "principal_investigator",
                                "projects",
                                "instrument",
                                "institution",
                                "experiments",
                                "dataset",
                            }:
                                nested_fieldtype = filter["target"][2]
                                if isinstance(filter["content"], list):
                                    Qdict = {"should": []}
                                    for option in filter["content"]:
                                        qry = Q(
                                            {
                                                "nested": {
                                                    "path": target_fieldtype,
                                                    "query": Q(
                                                        {
                                                            oper: {
                                                                ".".join(
                                                                    [
                                                                        target_fieldtype,
                                                                        nested_fieldtype,
                                                                    ]
                                                                ): option
                                                            }
                                                        }
                                                    ),
                                                }
                                            }
                                        )
                                        Qdict["should"].append(qry)
                                    query_obj_filt = Q({"bool": Qdict})
                                else:
                                    query_obj_filt = Q(
                                        {
                                            "nested": {
                                                "path": target_fieldtype,
                                                "query": Q(
                                                    {
                                                        oper: {
                                                            ".".join(
                                                                [
                                                                    target_fieldtype,
                                                                    nested_fieldtype,
                                                                ]
                                                            ): filter["content"]
                                                        }
                                                    }
                                                ),
                                            }
                                        }
                                    )
                                # Special handling for list of principal investigators
                                if target_fieldtype == "principal_investigator":
                                    Qdict_lr = {"should": [query_obj_filt]}
                                    if isinstance(filter["content"], list):
                                        Qdict = {"should": []}
                                        for option in filter["content"]:
                                            qry = Q(
                                                {
                                                    "nested": {
                                                        "path": target_fieldtype,
                                                        "query": Q(
                                                            {
                                                                "term": {
                                                                    ".".join(
                                                                        [
                                                                            target_fieldtype,
                                                                            "username",
                                                                        ]
                                                                    ): option
                                                                }
                                                            }
                                                        ),
                                                    }
                                                }
                                            )
                                            Qdict["should"].append(qry)
                                        query_obj_filt = Q({"bool": Qdict})
                                    else:
                                        query_obj_filt = Q(
                                            {
                                                "nested": {
                                                    "path": target_fieldtype,
                                                    "query": Q(
                                                        {
                                                            "term": {
                                                                ".".join(
                                                                    [
                                                                        target_fieldtype,
                                                                        "username",
                                                                    ]
                                                                ): filter["content"]
                                                            }
                                                        }
                                                    ),
                                                }
                                            }
                                        )
                                    Qdict_lr["should"].append(query_obj_filt)
                                    query_obj_filt = Q({"bool": Qdict_lr})
                                query_obj = query_obj & query_obj_filt

            # (4) Define fields not to return in the search results (for brevity)
            excluded_fields_list = [
                "end_time",
                "institution",
                "principal_investigator",
                "created_by",
                "end_time",
                "update_time",
                "instrument",
                "file_extension",
                "modification_time",
                "parameters.string.pn_id",
                "parameters.numerical.pn_id",
                "parameters.datetime.pn_id",
                "acls",
            ]
            if obj != "dataset":
                excluded_fields_list.append("description")

            ######TODO (5) Do some sorting
            # Default sorting
            sort_dict = {}
            if request_sorting is not None:
                if obj in request_sorting:
                    for sort in request_sorting[obj]:
                        if len(sort["field"]) > 1:
                            if sort["field"][-1] in {
                                "fullname",
                                "name",
                                "title",
                                "description",
                                "filename",
                            }:
                                search_field = ".".join(sort["field"]) + ".raw"
                            else:
                                search_field = ".".join(sort["field"])
                            sort_dict[search_field] = {
                                "order": sort["order"],
                                "nested_path": ".".join(sort["field"][:-1]),
                            }

                        if len(sort["field"]) == 1:
                            if sort["field"][0] in {
                                "principal_investigator",
                                "name",
                                "title",
                                "description",
                                "filename",
                            }:
                                sort_dict[sort["field"][0] + ".raw"] = {
                                    "order": sort["order"]
                                }
                            elif sort["field"][0] == "size":
                                if obj == "datafile":
                                    sort_dict[sort["field"][0]] = {
                                        "order": sort["order"]
                                    }
                                else:
                                    # DO SOME SORTING AFTER ELASTICSEARCH
                                    pass
                            else:
                                sort_dict[sort["field"][0]] = {"order": sort["order"]}

            # If sort dict is still empty even after filters, add in the defaults
            if not sort_dict:
                sort_dict = {match_list[idx] + ".raw": {"order": "asc"}}

            # (6) Add the search to the multi-search object, ready for execution
            ms = ms.add(
                Search(index=obj)
                .sort(sort_dict)
                .extra(size=RESULTS_PER_PAGE, min_score=MIN_CUTOFF_SCORE)
                .query(query_obj)
                .source(excludes=excluded_fields_list)
            )

        results = ms.execute()

        # --------------------
        # Post-search cleaning
        # --------------------

        # load in object IDs for all objects a user has sensitive access to
        # projects_sens = {*Project.safe.all(user, viewsensitive=True).values_list("id", flat=True)}
        projects_sens_query = (
            user.projectacls.select_related("project")
            .filter(canSensitive=True)
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("project__id", flat=True)
        )
        for group in groups:
            projects_sens_query |= (
                group.projectacls.select_related("project")
                .filter(canSensitive=True)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("project__id", flat=True)
            )
        projects_sens = [*projects_sens_query.distinct()]

        # experiments_sens = {*Experiment.safe.all(user, viewsensitive=True).values_list("id", flat=True)}
        experiments_sens_query = (
            user.experimentacls.select_related("experiment")
            .filter(canSensitive=True)
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("experiment__id", flat=True)
        )
        for group in groups:
            experiments_sens_query |= (
                group.experimentacls.select_related("experiment")
                .filter(canSensitive=True)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("experiment__id", flat=True)
            )
        experiments_sens = [*experiments_sens_query.distinct()]

        # datasets_sens = {*Dataset.safe.all(user, viewsensitive=True).values_list("id", flat=True)}
        datasets_sens_query = (
            user.datasetacls.select_related("dataset")
            .filter(canSensitive=True)
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("dataset__id", flat=True)
        )
        for group in groups:
            datasets_sens_query |= (
                group.datasetacls.select_related("dataset")
                .filter(canSensitive=True)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("dataset__id", flat=True)
            )
        datasets_sens = [*datasets_sens_query.distinct()]

        # datafiles_sens = {*DataFile.safe.all(user, viewsensitive=True).values_list("id", flat=True)}
        datafiles_sens_query = (
            user.datafileacls.select_related("datafile")
            .filter(canSensitive=True)
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("datafile__id", flat=True)
        )
        for group in groups:
            datafiles_sens_query |= (
                group.datafileacls.select_related("datafile")
                .filter(canSensitive=True)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("datafile__id", flat=True)
            )
        datafiles_sens = [*datafiles_sens_query.distinct()]

        # load in datafile IDs for all datafiles a user has download access to
        # datafiles_dl = {*DataFile.safe.all(user, downloadable=True).values_list("id", flat=True)}

        datafiles_dl_query = (
            user.datafileacls.select_related("datafile")
            .filter(canDownload=True)
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("datafile__id", flat=True)
        )
        for group in groups:
            datafiles_dl_query |= (
                group.datafileacls.select_related("datafile")
                .filter(canDownload=True)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("datafile__id", flat=True)
            )
        datafiles_dl = [*datafiles_dl_query.distinct()]

        # re-structure into convenient dictionary
        preloaded = {
            "project": {"sens_list": projects_sens, "objects": {}},
            "experiment": {"sens_list": experiments_sens, "objects": {}},
            "dataset": {"sens_list": datasets_sens, "objects": {}},
            "datafile": {"sens_list": datafiles_sens, "objects": {}},
        }
        # load in object IDs for all objects a user has read access to,
        # and IDs for all of the object's nested-children - regardless of user
        # access to these child objects (the access check come later)
        # projects_values = ["id", "experiment__id", "experiment__datasets__id",
        #                                         "experiment__datasets__datafile__id"]
        # projects = [*Project.safe.all(user).values_list(*projects_values)]

        projects_query = (
            user.projectacls.select_related("project")
            .prefetch_related(
                "project__experiments",
                "project__experiments__datasets",
                "project__experiments__datasets__datafile",
            )
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list(
                "project__id",
                "project__experiments__id",
                "project__experiments__datasets__id",
                "project__experiments__datasets__datafile__id",
            )
        )
        for group in groups:
            projects_query |= (
                group.projectacls.select_related("project")
                .prefetch_related(
                    "project__experiments",
                    "project__experiments__datasets",
                    "project__experiments__datasets__datafile",
                )
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list(
                    "project__id",
                    "project__experiments__id",
                    "project__experiments__datasets__id",
                    "project__experiments__datasets__datafile__id",
                )
            )
        projects = [*projects_query.distinct()]

        # experiments_values = ["id", "datasets__id", "datasets__datafile__id"]
        # experiments = [*Experiment.safe.all(user).values_list(*experiments_values)]

        experiments_query = (
            user.experimentacls.select_related("experiment")
            .prefetch_related("experiment__datasets", "experiment__datasets__datafile")
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list(
                "experiment__id",
                "experiment__datasets__id",
                "experiment__datasets__datafile__id",
            )
        )
        for group in groups:
            experiments_query |= (
                group.experimentacls.select_related("experiment")
                .prefetch_related(
                    "experiment__datasets", "experiment__datasets__datafile"
                )
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list(
                    "experiment__id",
                    "experiment__datasets__id",
                    "experiment__datasets__datafile__id",
                )
            )
        experiments = [*experiments_query.distinct()]

        # datasets = [*Dataset.safe.all(user).prefetch_related("datafile").values_list("id", "datafile__id")]
        datasets_query = (
            user.datasetacls.select_related("dataset")
            .prefetch_related("dataset__datafile")
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("dataset__id", "dataset__datafile__id")
        )
        for group in groups:
            datasets_query |= (
                group.datasetacls.select_related("dataset")
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("dataset__id", "dataset__datafile__id")
            )
        datasets = [*datasets_query.distinct()]

        # datafiles = [*DataFile.safe.all(user).values_list("id", "size")]
        datafiles_query = (
            user.datafileacls.select_related("datafile")
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("datafile__id", "datafile__size")
        )
        for group in groups:
            datafiles_query |= (
                group.datafileacls.select_related("datafile")
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("datafile__id", "datafile__size")
            )
        datafiles = [*datafiles_query.distinct()]

        # add data to preloaded["objects"] dictionary with ID as key and nested items as value - key/values.
        # Probably a cleaner/simpler way to do this, but hey ho!
        for key, value in {
            "project": projects,
            "experiment": experiments,
            "dataset": datasets,
            "datafile": datafiles,
        }.items():
            for item in value:
                name = item[0]
                if name in preloaded[key]["objects"]:
                    if key == "dataset":
                        preloaded[key]["objects"][name]["dfs"].add(item[1])
                    elif key == "experiment":
                        preloaded[key]["objects"][name]["sets"].add(item[1])
                        preloaded[key]["objects"][name]["dfs"].add(item[2])
                    elif key == "project":
                        preloaded[key]["objects"][name]["exps"].add(item[1])
                        preloaded[key]["objects"][name]["sets"].add(item[2])
                        preloaded[key]["objects"][name]["dfs"].add(item[3])
                else:
                    new_dict = {}
                    if key == "datafile":
                        new_dict["size"] = item[1]
                    elif key == "dataset":
                        new_dict["dfs"] = {item[1]}
                    elif key == "experiment":
                        new_dict["sets"] = {item[1]}
                        new_dict["dfs"] = {item[2]}
                    elif key == "project":
                        new_dict["exps"] = {item[1]}
                        new_dict["sets"] = {item[2]}
                        new_dict["dfs"] = {item[3]}
                    preloaded[key]["objects"][name] = new_dict

        # Create the result object which will be returned to the front-end
        result_dict = {k: [] for k in ["project", "experiment", "dataset", "datafile"]}

        # If filters are active, enforce the "parent in results" criteria on relevant objects
        if filter_level:
            # Define parent_type for experiment/datafile (N/A for project, hardcoded for dataset)
            parent_child = {"experiment": "projects", "dataset": "experiments"}
            # Define hierarchy of types for filter levels
            hierarch = [3, 2, 1]  # {"experiments":3, "datasets":2, "datafiles":1}
            for idx, item in enumerate(results[1:]):
                # if active filter level higher than current object type: apply "parent-in-result" filter
                if hierarch[idx] < filter_level:

                    parent_ids = [
                        objj["_source"]["id"] for objj in results[idx].hits.hits
                    ]
                    parent_ids_set = {*parent_ids}

                    for obj_idx, obj in reversed([*enumerate(item.hits.hits)]):
                        if obj["_index"] != "datafile":
                            parent_es_ids = [
                                parent["id"]
                                for parent in obj["_source"][
                                    parent_child[obj["_index"]]
                                ]
                            ]
                            if not any(itemm in parent_es_ids for itemm in parent_ids):
                                results[idx + 1].hits.hits.pop(obj_idx)
                        else:
                            if (
                                obj["_source"]["dataset"]["id"] not in parent_ids_set
                            ):  # parent object is idx-1, but idx in enumerate is already shifted by -1, so straight idx
                                results[idx + 1].hits.hits.pop(obj_idx)
        # Count the number of search results after elasticsearch + parent filtering
        total_hits = {
            index_list[idx]: len(type.hits.hits) for idx, type in enumerate(results)
        }

        for item in results:
            item.hits.hits = item.hits.hits[
                request_offset : (request_offset + request_size)
            ]

        # Pagination done before final cleaning to reduce "clean_parent_ids" duration
        # Default Pagination handled by response.get if key isn't specified
        # result_dict = {k:v[request_offset:(request_offset+request_size)] for k,v in result_dict.items()}

        # Clean and prepare the results "hit" objects and append them to the results_dict
        for item in results:
            for hit_attrdict in item.hits.hits:
                hit = hit_attrdict.to_dict()

                # Check to see if indexed object actually exists in DB, if not then skip
                if int(hit["_source"]["id"]) not in preloaded[hit["_index"]]["objects"]:
                    continue

                # Default sensitive permission and size of object
                sensitive_bool = False
                size = 0
                # If user/group has sensitive permission, update flag
                if hit["_source"]["id"] in preloaded[hit["_index"]]["sens_list"]:
                    sensitive_bool = True
                # Re-package parameters into single parameter list
                param_list = []
                if "string" in hit["_source"]["parameters"]:
                    param_list.extend(hit["_source"]["parameters"]["string"])
                if "numerical" in hit["_source"]["parameters"]:
                    param_list.extend(hit["_source"]["parameters"]["numerical"])
                if "datetime" in hit["_source"]["parameters"]:
                    param_list.extend(hit["_source"]["parameters"]["datetime"])
                hit["_source"]["parameters"] = param_list
                # Remove unused fields to reduce data sent to front-end
                hit.pop("_score")
                hit.pop("_id")
                hit.pop("_type")
                hit.pop("sort")

                # Get count of all nested objects and download status
                if hit["_index"] == "datafile":

                    if hit["_source"]["id"] in datafiles_dl:
                        hit["_source"]["userDownloadRights"] = "full"
                        size = hit["_source"]["size"]
                    else:
                        hit["_source"]["userDownloadRights"] = "none"

                else:
                    safe_nested_dfs_set = {
                        *preloaded["datafile"]["objects"]
                    }.intersection(
                        preloaded[hit["_index"]]["objects"][hit["_source"]["id"]]["dfs"]
                    )
                    safe_nested_dfs_count = len(safe_nested_dfs_set)
                    if hit["_index"] in {"project", "experiment"}:
                        safe_nested_set = len(
                            {*preloaded["dataset"]["objects"]}.intersection(
                                preloaded[hit["_index"]]["objects"][
                                    hit["_source"]["id"]
                                ]["sets"]
                            )
                        )
                    # Ugly hack, should do a nicer, less verbose loop+type detection
                    if hit["_index"] == "project":
                        safe_nested_exp = len(
                            {*preloaded["experiment"]["objects"]}.intersection(
                                preloaded[hit["_index"]]["objects"][
                                    hit["_source"]["id"]
                                ]["exps"]
                            )
                        )
                        hit["_source"]["counts"] = {
                            "experiments": safe_nested_exp,
                            "datasets": safe_nested_set,
                            "datafiles": (safe_nested_dfs_count),
                        }
                    if hit["_index"] == "experiment":
                        hit["_source"]["counts"] = {
                            "datasets": safe_nested_set,
                            "datafiles": safe_nested_dfs_count,
                        }
                    if hit["_index"] == "dataset":
                        hit["_source"]["counts"] = {"datafiles": safe_nested_dfs_count}
                    # Get downloadable datafiles ultimately belonging to this "hit" object
                    # and calculate the total size of these files
                    safe_nested_dfs_dl = [
                        *safe_nested_dfs_set.intersection(datafiles_dl)
                    ]
                    size = sum(
                        [
                            preloaded["datafile"]["objects"][id]["size"]
                            for id in safe_nested_dfs_dl
                        ]
                    )
                    # Determine the download state of the "hit" object
                    # safe_nested_dfs_dl_bool = [id in datafiles_dl for id in safe_nested_dfs]
                    if safe_nested_dfs_set.issubset(datafiles_dl):
                        hit["_source"]["userDownloadRights"] = "full"
                    elif safe_nested_dfs_set.intersection(datafiles_dl):
                        hit["_source"]["userDownloadRights"] = "partial"
                    else:
                        hit["_source"]["userDownloadRights"] = "none"

                hit["_source"]["size"] = filesizeformat(size)

                # if no sensitive access, remove sensitive metadata from response
                for idxx, parameter in reversed(
                    [*enumerate(hit["_source"]["parameters"])]
                ):
                    if not sensitive_bool:
                        if parameter["sensitive"]:
                            hit["_source"]["parameters"].pop(idxx)
                        else:
                            hit["_source"]["parameters"][idxx].pop("sensitive")
                    else:
                        if not parameter["sensitive"]:
                            hit["_source"]["parameters"][idxx].pop("sensitive")

                # Append hit to results if not already in results.
                # Due to non-identical scores in hits for non-sensitive vs sensitive search,
                # we require a more complex comparison than just 'is in' as hits are not identical
                # if hit["_source"]['id'] not in [objj["_source"]['id'] for objj in result_dict[hit["_index"]+"s"]]:
                result_dict[hit["_index"]].append(hit)

        # Removes parent IDs from hits once parent-filtering applied
        # Removed for tidiness in returned response to front-end
        # Define parent_type for experiment/datafile (N/A for project)
        parent_child = {
            "experiment": "projects",
            "dataset": "experiments",
            "datafile": "dataset",
        }
        for objs in ["experiment", "dataset", "datafile"]:
            for obj_idx, obj in reversed([*enumerate(result_dict[objs])]):
                del result_dict[objs][obj_idx]["_source"][parent_child[obj["_index"]]]

        # If individual object type requested, limit the returned values to that object type
        if request_type is not None:
            result_dict = {request_type: result_dict.pop(request_type)}
            total_hits = {request_type: total_hits.pop(request_type)}

        # add search results to bundle, and return bundle
        bundle.obj = SearchObject(id=1, hits=result_dict, total_hits=total_hits)
        return bundle

    # def get_object_list(self, request):
    #    user = request.user
    #    query_text = request.GET.get("query", None)
    #    if not user.is_authenticated:
    #        result_dict = simple_search_public_data(query_text)
    #        return [SearchObject(id=1, hits=result_dict)]
    #    groups = user.groups.all()
    #    index_list = ["experiments", "dataset", "datafile"]
    #    ms = MultiSearch(index=index_list)
    #    query_exp = Q("match", title=query_text)
    #    query_exp_oacl = Q("term", acls__entityId=user.id) | Q(
    #        "term", public_access=100
    #    )
    #    for group in groups:
    #        query_exp_oacl = query_exp_oacl | Q("term", acls__entityId=group.id)
    #    query_exp = query_exp & query_exp_oacl
    #    ms = ms.add(
    #        Search(index="experiments")
    #        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
    #        .query(query_exp)
    #    )
    #    query_dataset = Q("match", description=query_text)
    #    query_dataset_oacl = Q("term", acls__entityId=user.id) | Q(
    #        "term", public_access=100
    #    )
    #    for group in groups:
    #        query_dataset_oacl = query_dataset_oacl | Q("term", acls__entityId=group.id)
    #    query_dataset = query_dataset & query_dataset_oacl
    #    ms = ms.add(
    #        Search(index="dataset")
    #        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
    #        .query(query_dataset)
    #    )
    #    query_datafile = Q("match", filename=query_text)
    #    query_datafile_oacl = Q("term", acls__entityId=user.id) | Q(
    #        "term", public_access=100
    #    )
    #    for group in groups:
    #        query_datafile_oacl = query_datafile_oacl | Q(
    #            "term", acls__entityId=group.id
    #        )
    #    query_datafile = query_datafile & query_datafile_oacl
    #    ms = ms.add(
    #        Search(index="datafile")
    #        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
    #        .query(query_datafile)
    #    )
    #    results = ms.execute()
    #    result_dict = {k: [] for k in ["experiments", "datasets", "datafiles"]}
    #    for item in results:
    #        for hit in item.hits.hits:
    #            if hit["_index"] == "dataset":
    #                result_dict["datasets"].append(hit.to_dict())
    #            elif hit["_index"] == "experiments":
    #                result_dict["experiments"].append(hit.to_dict())
    #            elif hit["_index"] == "datafile":
    #                result_dict["datafiles"].append(hit.to_dict())
    #    return [SearchObject(id=1, hits=result_dict)]
