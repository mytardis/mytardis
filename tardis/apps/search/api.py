'''
RESTful API for MyTardis search.
Implemented with Tastypie.

.. moduleauthor:: Manish Kumar <rishimanish123@gmail.com>
'''
import json
import datetime
import pytz

from django.conf import settings

from tastypie import fields
from tastypie.resources import Resource, Bundle
from tastypie.serializers import Serializer
from django_elasticsearch_dsl.search import Search
from elasticsearch_dsl import MultiSearch, Q
from django.template.defaultfilters import filesizeformat

from tardis.tardis_portal.api import default_authentication
from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import (Project, Experiment, Dataset, DataFile,
                                         Instrument, ExperimentParameter,
                                         DatasetParameter, DatafileParameter,
                                         Schema, ParameterName)

import logging

LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)
MAX_SEARCH_RESULTS = settings.MAX_SEARCH_RESULTS
MIN_CUTOFF_SCORE = settings.MIN_CUTOFF_SCORE

class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        logging.info("The data is " + str(data))
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data, cls=json.JSONEncoder,
                          sort_keys=True, ensure_ascii=False,
                          indent=self.json_indent) + "\n"


if settings.DEBUG:
    default_serializer = PrettyJSONSerializer()
else:
    default_serializer = Serializer()


class SearchObject(object):
    def __init__(self, hits=None, id=None):
        self.hits = hits
        self.id = id


class SchemasObject(object):
    def __init__(self, schemas=None, id=None):
        self.schemas = schemas
        self.id = id


class SchemasAppResource(Resource):
    """Tastypie resource for schemas"""
    schemas = fields.ApiField(attribute='schemas', null=True)

    class Meta:
        resource_name = 'get-schemas'
        list_allowed_methods = ['get']
        serializer = default_serializer
        authentication = default_authentication
        object_class = SchemasObject
        always_return_data = True

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.id
        else:
            kwargs['pk'] = bundle_or_obj['id']

        return kwargs

    def get_object_list(self, request):
        logging.warn("Testing search app: get schemas")
        if not request.user.is_authenticated:
            result_dict = {
                           "projects" : None,
                           "experiments" : None,
                           "datasets" : None,
                           "datafiles" : None
                           }
            return [SchemasObject(id=1, schemas=result_dict)]
        result_dict = {
                       "projects" : list(set(list(Project.safe.all(request.user
                                    ).prefetch_related('projectparameterset'
                                    ).values_list("projectparameterset__schema__id", flat=True)))),
                       "experiments" : list(set(list(Experiment.safe.all(request.user
                                       ).prefetch_related('experimentparameterset'
                                       ).values_list("experimentparameterset__schema__id", flat=True)))),
                       "datasets" : list(set(list(Dataset.safe.all(request.user
                                       ).prefetch_related('datasetparameterset'
                                       ).values_list("datasetparameterset__schema__id", flat=True)))),
                       "datafiles" : list(set(list(DataFile.safe.all(request.user
                                       ).prefetch_related('datafileparameterset'
                                       ).values_list("datafileparameterset__schema__id", flat=True))))
                       }
        safe_dict = {}
        for key in result_dict:
            safe_dict[key] = {}
            for value in result_dict[key]:
                if value is not None:
                    schema_id = str(value)
                    schema_dict = {
                                   "id" : schema_id,
                                   "type" : key,
                                   "schema_name" : Schema.objects.get(id=value).name,
                                   "parameters": {}
                                   }
                    param_names = ParameterName.objects.filter(schema__id=value)
                    for param in param_names:
                        type_dict = {1:"NUMERIC",
                                     2:"STRING",
                                     3:"URL",
                                     4:"LINK",
                                     5:"FILENAME",
                                     6:"DATETIME",
                                     7:"LONGSTRING",
                                     8:"JSON"}
                        param_id = str(param.id)
                        param_dict = {
                                      "id" : param_id,
                                      "full_name": param.full_name,
                                      "data_type": type_dict[param.data_type]
                                      }
                        schema_dict["parameters"][param_id] = param_dict
                    safe_dict[key][schema_id] = schema_dict

        return [SchemasObject(id=1, schemas=safe_dict)]


    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


class SearchAppResource(Resource):
    """Tastypie resource for simple-search"""
    hits = fields.ApiField(attribute='hits', null=True)

    class Meta:
        resource_name = 'simple-search'
        list_allowed_methods = ['post']
        serializer = default_serializer
        authentication = default_authentication
        object_class = SearchObject
        always_return_data = True

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.id
        else:
            kwargs['pk'] = bundle_or_obj['id']

        return kwargs


    def get_object_list(self, request):
        return request


    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


    def obj_create(self, bundle, **kwargs):
        bundle = self.dehydrate(bundle)
        return bundle


    def dehydrate(self, bundle):
        logging.warn("Testing search app")
        user = bundle.request.user

        query_text = bundle.data.get('query', None)

        filters = bundle.data.get('filters', None)

        if not user.is_authenticated:
            result_dict = simple_search_public_data(query_text)
            return [SearchObject(id=1, hits=result_dict)]
        groups = user.groups.all()
        index_list = ['project', 'experiment', 'dataset', 'datafile']
        match_list = ['name','title','description','filename']
        filter_level = 0

        ms = MultiSearch(index=index_list)

        for idx, obj in enumerate(index_list):

            # add user/group criteria to searchers
            query_obj =  Q({"nested" : {
                "path":"objectacls", "query": Q(
                    {"bool": {"must":[
                        Q({"match": {"objectacls.entityId":user.id}}),
                        Q({"term": {"objectacls.pluginId":"django_user"}})
                    ]}}
                )
            }})

            for group in groups:

                query_obj_group =  Q({"nested" : {
                    "path":"objectacls", "query": Q(
                        {"bool": {"must":[
                            Q({"match": {"objectacls.entityId":group.id}}),
                            Q({"term": {"objectacls.pluginId":"django_group"}})
                        ]}}
                    )
                }})

                query_obj = query_obj | query_obj_group


            if query_text is not None:
                if query_text is not "":

                    # Search on title/keywords + on non-sensitive metadata
                    query_obj_text = Q({"match": {match_list[idx]:query_text}})
                    query_obj_text_meta = Q(
                        {"nested" : {
                            "path":"parameters.string", "query": Q(
                                {"bool": {"must":[
                                    Q({"match": {"parameters.string.value":query_text}}),
                                    Q({"term": {"parameters.string.sensitive":False}})
                                ]}}
                            )
                        }})
                    query_obj_text_meta = query_obj_text | query_obj_text_meta

                    query_obj = query_obj & query_obj_text_meta


            if filters is not None:
                #filter_level = True
                #filter_op = filters['op']     This isn't used for now
                filterlist = filters["content"]
                operator_dict = {"is":"term", "contains":"match", ">=":"gte", "<=" : "lte"}
                num_2_type = {1:'experiment', 2:'dataset', 3:'datafile', 11:'project'}
                hierarchy = {'project':4, 'experiment':3, 'dataset':2, 'datafile':1}

                for filter in filterlist:
                    oper = operator_dict[filter['op']]

                    if filter["kind"] == "schemaParameter":
                        schema_id, param_id = filter["target"][0], filter["target"][1]
                        # check filter is applied to correct object type
                        if num_2_type[Schema.objects.get(id=schema_id).schema_type] == obj:
                            if filter_level < hierarchy[obj]:
                                filter_level = hierarchy[obj]
                            if filter["type"] == "STRING":
                                # check if filter query is list of options, or single value
                                # (elasticsearch can actually handle delimiters in a single string...)
                                if isinstance(filter["content"], list):
                                    Qdict = {"should" : []}
                                    for option in filter["content"]:
                                        qry = Q(
                                            {"nested" : {
                                                "path":"parameters.string", "query": Q(
                                                    {"bool": {"must":[
                                                        Q({"match": {"parameters.string.pn_id":str(param_id)}}),
                                                        Q({oper: {"parameters.string.value":option}})
                                                    ]}}
                                                )
                                            }})
                                        Qdict["should"].append(qry)
                                    query_obj_filt = Q({"bool" : Qdict})
                                else:
                                    query_obj_filt = Q(
                                        {"nested" : {
                                            "path":"parameters.string", "query": Q(
                                                {"bool": {"must":[
                                                    Q({"match": {"parameters.string.pn_id":str(param_id)}}),
                                                    Q({oper: {"parameters.string.value":filter["content"]}})
                                                ]}}
                                            )
                                        }})
                            elif filter["type"] == "NUMERIC":
                                query_obj_filt = Q(
                                    {"nested" : {
                                        "path":"parameters.numerical", "query": Q(
                                            {"bool": {"must":[
                                                Q({"match": {"parameters.numerical.pn_id":str(param_id)}}),
                                                Q({"range": {"parameters.numerical.value": {oper:filter["content"]}}})
                                            ]}}
                                        )
                                    }})
                            elif filter["type"] == "DATETIME":
                                query_obj_filt = Q(
                                    {"nested" : {
                                        "path":"parameters.datetime", "query": Q(
                                            {"bool": {"must":[
                                                Q({"match": {"parameters.datetime.pn_id":str(param_id)}}),
                                                Q({"range": {"parameters.datetime.value": {oper:filter["content"]}}})
                                            ]}}
                                        )
                                    }})
                            query_obj = query_obj & query_obj_filt

                    if filter["kind"] == "typeAttribute":
                        target_objtype, target_fieldtype = filter["target"][0], filter["target"][1]
                        if target_objtype == obj+"s":
                            if filter_level < hierarchy[obj]:
                                filter_level = hierarchy[obj]
                            if target_fieldtype == "schema":
                                # check if filter query is list of options, or single value
                                if isinstance(filter["content"], list):
                                    Qdict = {"should" : []}
                                    for option in filter["content"]:
                                        qry = Q(
                                            {"nested" : {
                                                "path":"parameters.schemas", "query": Q(
                                                        {oper: {"parameters.schemas.schema_id":option}}
                                                )
                                            }})
                                        Qdict["should"].append(qry)
                                    query_obj_filt = Q({"bool" : Qdict})
                                else:
                                    query_obj_filt = Q(
                                        {"nested" : {
                                            "path":"parameters.schemas", "query": Q(
                                                    {oper: {"parameters.schemas.schema_id":filter["content"]}}
                                            )
                                        }})

                                query_obj = query_obj & query_obj_filt

                            # Fields that are intrinsic to the object (Proj,exp,set,file)
                            if target_fieldtype in ['name', 'description', 'title',
                                                    'tags', 'filename', 'file_extension',
                                                    'created_time', 'start_date', 'end_date']:

                                if filter["type"] == "STRING":

                                    if isinstance(filter["content"], list):
                                        Qdict = {"should" : []}
                                        for option in filter["content"]:
                                            if target_fieldtype == "file_extension":
                                                if option[0] == ".":
                                                    option = option[1:]
                                            qry = Q({oper: {target_fieldtype:option}})
                                            Qdict["should"].append(qry)
                                        query_obj_filt = Q({"bool" : Qdict})
                                    else:
                                        if target_fieldtype == "file_extension":
                                            if filter["content"][0] == ".":
                                                filter["content"] = filter["content"][1:]
                                        query_obj_filt = Q({oper: {target_fieldtype:filter["content"]}})

                                elif filter["type"] == "DATETIME":
                                        query_obj_filt = Q({"range": {target_fieldtype: {oper:filter["content"]}}})


                                query_obj = query_obj & query_obj_filt


                            # Fields that are intrinsic to related objects (instruments, users, etc)
                            if target_fieldtype in ['lead_researcher', 'project', 'instrument',
                                                    'institution', 'experiments', 'dataset']:
                                nested_fieldtype = filter["target"][2]

                                if isinstance(filter["content"], list):
                                    Qdict = {"should" : []}
                                    for option in filter["content"]:
                                        qry = Q(
                                            {"nested" : {
                                                "path":target_fieldtype, "query": Q(
                                                        {oper: {".".join([target_fieldtype,nested_fieldtype]):option}}
                                                )
                                            }})
                                        Qdict["should"].append(qry)
                                    query_obj_filt = Q({"bool" : Qdict})
                                else:
                                    query_obj_filt = Q(
                                        {"nested" : {
                                            "path":target_fieldtype, "query": Q(
                                                    {oper: {".".join([target_fieldtype,nested_fieldtype]):filter["content"]}}
                                            )
                                        }})

                                if target_fieldtype == 'lead_researcher':
                                    Qdict_lr = {"should" : [query_obj_filt]}

                                    if isinstance(filter["content"], list):
                                        Qdict = {"should" : []}
                                        for option in filter["content"]:
                                            qry = Q(
                                                {"nested" : {
                                                    "path":target_fieldtype, "query": Q(
                                                            {'term': {".".join([target_fieldtype,'username']):option}}
                                                    )
                                                }})
                                            Qdict["should"].append(qry)
                                        query_obj_filt = Q({"bool" : Qdict})
                                    else:
                                        query_obj_filt = Q(
                                            {"nested" : {
                                                "path":target_fieldtype, "query": Q(
                                                        {'term': {".".join([target_fieldtype,'username']):filter["content"]}}
                                                )
                                            }})
                                    Qdict_lr["should"].append(query_obj_filt)
                                    query_obj_filt = Q({"bool" : Qdict_lr})

                                query_obj = query_obj & query_obj_filt

            excluded_fields_list = ["end_date", "institution", "lead_researcher", "created by",
                                    "end_time", "update_time", "instrument", "file_extension",
                                    "modification_time", "parameters.string.pn_id",
                                    "parameters.numerical.pn_id", "parameters.datetime.pn_id",
                                    'objectacls'] #"experiments", 'dataset', 'project',

                                    #
                                    #"parameters.string.sensitive","parameters.numerical.sensitive","parameters.datetime.sensitive",
            if obj != 'dataset':
                excluded_fields_list.append('description')


            ms = ms.add(Search(index=obj)
                        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                        .query(query_obj).source(excludes=excluded_fields_list) )


        results = ms.execute()

        # load in sensitive IDs
        projects_sens = Project.safe.all(user, viewsensitive=True).values_list("id", flat=True)
        experiments_sens = Experiment.safe.all(user, viewsensitive=True).values_list("id", flat=True)
        datasets_sens = Dataset.safe.all(user, viewsensitive=True).values_list("id", flat=True)
        datafiles_sens = DataFile.safe.all(user, viewsensitive=True).values_list("id", flat=True)

        # load in downloadable datafile IDs
        datafiles_dl = DataFile.safe.all(user, downloadable=True).values_list("id", flat=True)

        # convenient list
        preloaded = {
                     "project": {"sens_list" : projects_sens,
                                 "objects" : {}},
                     "experiment": {"sens_list" : experiments_sens,
                                 "objects" : {}},
                     "dataset": {"sens_list" : datasets_sens,
                                 "objects" : {}},
                     "datafile": {"sens_list" : datafiles_sens,
                                  "objects" : {}},
        }

        # load in accessable IDs and all related child IDs
        projects = list(Project.safe.all(user).values("id", "experiment__id", "experiment__datasets__id",
                                                 "experiment__datasets__datafile__id"))
        experiments = list(Experiment.safe.all(user).values("id", "datasets__id", "datasets__datafile__id"))
        datasets = list(Dataset.safe.all(user).values("id", "datafile__id"))
        datafiles = list(DataFile.safe.all(user).values("id", "size"))

        # add data to preloaded["objects"] dictionary with ID as key and nested items as value - key/values.
        for key, value in {'project': projects, 'experiment':experiments, "dataset":datasets, "datafile":datafiles}.items():
            for item in value:
                name = item.pop('id')
                if name in preloaded[key]["objects"]:

                    if key == "project":
                        preloaded[key]["objects"][name]["exps"].append(item.pop("experiment__id"))
                        preloaded[key]["objects"][name]["sets"].append(item.pop("experiment__datasets__id"))
                        preloaded[key]["objects"][name]["dfs"].append(item.pop("experiment__datasets__datafile__id"))

                    if key == "experiment":
                        preloaded[key]["objects"][name]["sets"].append(item.pop("datasets__id"))
                        preloaded[key]["objects"][name]["dfs"].append(item.pop("datasets__datafile__id"))

                    if key == "dataset":
                        preloaded[key]["objects"][name]["dfs"].append(item.pop("datafile__id"))

                else:
                    new_dict = {}
                    if key == "project":
                        new_dict["exps"] = [item.pop("experiment__id")]
                        new_dict["sets"] = [item.pop("experiment__datasets__id")]
                        new_dict["dfs"] = [item.pop("experiment__datasets__datafile__id")]

                    if key == "experiment":
                        new_dict["sets"] = [item.pop("datasets__id")]
                        new_dict["dfs"] = [item.pop("datasets__datafile__id")]

                    if key == "dataset":
                        new_dict["dfs"] = [item.pop("datafile__id")]

                    if key == "datafile":
                        new_dict["size"] = item.pop("size")

                    preloaded[key]["objects"][name] = new_dict


        result_dict = {k: [] for k in ["projects", "experiments", "datasets", "datafiles"]}

        def clean_response(request, results, result_dict, sensitive=False):
            for item in results:
                for hit in item.hits.hits:

                    # Default sensitive permission and size of object
                    sensitive_bool = False
                    size = 0

                    # If user/group has sensitive permission, update flag
                    if hit["_source"]["id"] in preloaded[hit["_index"]]['sens_list']:
                        sensitive_bool = True

                    # Get total/nested size of object, respecting ACL access to child objects
                    #size = #authz.get_nested_size(request, hit["_source"]["id"], hit["_index"])

                    # Must work on copy of current iterable <- only if iterable length changes
                    #safe_hit = hit.copy()

                    # Remove ACLs and add size to repsonse

                    #hit["_source"].pop("objectacls")
                    #hit["_source"].pop("parameters")
                    param_list = []
                    if "string" in hit["_source"]["parameters"]:
                        param_list.extend(hit["_source"]["parameters"]["string"])
                    if "numerical" in hit["_source"]["parameters"]:
                        param_list.extend(hit["_source"]["parameters"]["numerical"])
                    if "datetime" in hit["_source"]["parameters"]:
                        param_list.extend(hit["_source"]["parameters"]["datetime"])
                    hit["_source"]["parameters"] = param_list
                    hit.pop("_score")
                    hit.pop("_id")
                    hit.pop("_type")


                    # Get count of all nested objects and download status
                    if hit["_index"] != 'datafile':

                        safe_nested_dfs = list(set(preloaded["datafile"]["objects"].keys()).intersection(list(
                                                preloaded[hit["_index"]]["objects"][hit["_source"]["id"]]['dfs'])))
                        if hit["_index"] in ["project", "experiment"]:
                            safe_nested_set= len(set(preloaded["dataset"]["objects"].keys()).intersection(list(
                                                    preloaded[hit["_index"]]["objects"][hit["_source"]["id"]]['sets'])))

                        # Ugly hack, should do a nicer, less verbose loop+type detection
                        if hit["_index"] == 'project':
                            safe_nested_exp = len(set(preloaded["experiment"]["objects"].keys()).intersection(list(
                                                    preloaded[hit["_index"]]["objects"][hit["_source"]["id"]]['exps'])))
                            hit["_source"]["counts"] = {"experiments" :safe_nested_exp,
                                                        "datasets" : safe_nested_set,
                                                        "datafiles": len(safe_nested_dfs)}

                        if hit["_index"] == 'experiment':
                            hit["_source"]["counts"] = {"datasets" : safe_nested_set,
                                                        "datafiles": len(safe_nested_dfs)}

                        if hit["_index"] == 'dataset':
                            hit["_source"]["counts"] = {"datafiles": len(safe_nested_dfs)}

                        safe_nested_dfs_dl = list(set(safe_nested_dfs).intersection(datafiles_dl))

                        #for id in safe_nested_dfs_dl:
                        #    size = preloaded[hit["_index"]]["objects"]["size"]

                        size = sum([preloaded["datafile"]["objects"][id]["size"] for id in safe_nested_dfs_dl])

                        safe_nested_dfs_dl_bool = [id in datafiles_dl for id in safe_nested_dfs]

                        if all(safe_nested_dfs_dl_bool):
                            hit["_source"]["userDownloadRights"] = 'full'
                        elif any(safe_nested_dfs_dl_bool):
                            hit["_source"]["userDownloadRights"] = 'partial'
                        else:
                            hit["_source"]["userDownloadRights"] = 'none'

                    else:
                        if hit["_source"]["id"] in datafiles_dl:
                            hit["_source"]["userDownloadRights"] = "full"
                            size = hit["_source"]["size"]
                        else:
                            hit["_source"]["userDownloadRights"] = "none"

                    hit["_source"]["size"] = filesizeformat(size)


                    # if no sensitive access, remove sensitive metadata from response
                    for idxx, parameter in enumerate(hit["_source"]["parameters"]):
                        if not sensitive_bool:
                            if parameter['sensitive']:
                                hit["_source"]["parameters"].pop(idxx)
                            else:
                                hit["_source"]["parameters"][idxx].pop("sensitive")

                        else:
                            hit["_source"]["parameters"][idxx].pop("sensitive")

                    # Append hit to final results if not already in results.
                    # Due to non-identical scores in hits for non-sensitive vs sensitive search,
                    # we require a more complex comparison than just 'is in' as hits are not identical
                    if hit["_source"]['id'] not in [objj["_source"]['id'] for objj in result_dict[hit["_index"]+"s"]]:
                        result_dict[hit["_index"]+"s"].append(hit)


        def filter_parent_child(result_dict, filter_level):

            # Define parent_type for experiment/datafile (N/A for project, hardcoded for dataset)
            parent_child = {"experiment":"project", "datafile":"dataset"}

            # Define hierarchy of types for filter levels
            hierarchy = {"experiments":3, "datasets":2, "datafiles":1}
            for objs in ["experiments", "datasets", "datafiles"]:
                if hierarchy[objs] < filter_level:
                    for obj_idx, obj in reversed(list(enumerate(result_dict[objs]))):
                        if obj["_index"] != 'dataset':
                            if obj["_source"][parent_child[obj["_index"]]]["id"] not in [objj["_source"]['id'] \
                                    for objj in result_dict[parent_child[obj["_index"]]+"s"]]:
                                result_dict[objs].pop(obj_idx)
                        else:
                            exp_ids = [parent['id'] for parent in obj["_source"]["experiments"]]
                            if not any(item in exp_ids for item in [objj["_source"]['id'] for objj in result_dict["experiments"]]):
                                result_dict[objs].pop(obj_idx)


        def final_clean(result_dict):
            # Define parent_type for experiment/datafile (N/A for project)
            parent_child = {"experiment":"project", "dataset":"experiments", "datafile":"dataset"}
            for objs in ["experiments", "datasets", "datafiles"]:
                for obj_idx, obj in reversed(list(enumerate(result_dict[objs]))):
                    del result_dict[objs][obj_idx]["_source"][parent_child[obj["_index"]]]


        clean_response(bundle.request, results, result_dict)

        if filter_level:
            filter_parent_child(result_dict, filter_level)

        final_clean(result_dict)

        # add search results to bundle, and return bundle
        bundle.obj = SearchObject(id=1, hits=result_dict)
        return bundle


# WARNING: This is busted
def simple_search_public_data(query_text):
    result_dict = {k: [] for k in ["experiments", "datasets", "datafiles"]}
    index_list = ['experiment', 'dataset', 'datafile']
    ms = MultiSearch(index=index_list)
    query_exp = Q("match", title=query_text)
    query_exp_oacl = Q("term", public_access=100)
    query_exp = query_exp & query_exp_oacl
    ms = ms.add(Search(index='experiment')
                .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                .query(query_exp))
    query_dataset = Q("match", description=query_text)
    query_dataset = query_dataset | Q("match", tags=query_text)
    query_dataset_oacl = Q("term", **{'experiment.public_access': 100})
    ms = ms.add(Search(index='dataset')
                .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE).query(query_dataset)
                .query('nested', path='experiment', query=query_dataset_oacl))
    query_datafile = Q("match", filename=query_text)
    query_datafile_oacl = Q("term", **{'dataset.experiment.public_access': 100})
    ms = ms.add(Search(index='datafile')
                .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE).query(query_datafile)
                .query('nested', path='dataset.experiment', query=query_datafile_oacl))
    results = ms.execute()
    for item in results:
        for hit in item.hits.hits:
            #safe_hit = hit.copy()
            hit["_source"].pop("objectacls")
            result_dict[hit["_index"]+'s'].append(hit)

    return result_dict
