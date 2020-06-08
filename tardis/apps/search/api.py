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
                                         DatasetParameter, DatafileParameter)

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


class SearchAppResource(Resource):
    """Tastypie resource for simple-search"""
    hits = fields.ApiField(attribute='hits', null=True)

    class Meta:
        resource_name = 'simple-search'
        list_allowed_methods = ['get']
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
        logging.warn("Testing search app")
        user = request.user
        query_text = request.GET.get('query', None)
        if not user.is_authenticated:
            result_dict = simple_search_public_data(query_text)
            return [SearchObject(id=1, hits=result_dict)]
        groups = user.groups.all()
        index_list = ['project', 'experiment', 'dataset', 'datafile']
        ms = MultiSearch(index=index_list)

        query_project = Q("match", name=query_text)
        query_project_oacl = Q("term", objectacls__entityId=user.id) #| \Q("term", public_access=100)
        for group in groups:
            query_project_oacl = query_project_oacl | \
                                 Q("term", objectacls__entityId=group.id)
        query_project = query_project & query_project_oacl
        ms = ms.add(Search(index='project')
                    .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                    .query(query_project))

        query_exp = Q("match", title=query_text)
        query_exp_oacl = Q("term", objectacls__entityId=user.id) #| \Q("term", public_access=100)
        for group in groups:
            query_exp_oacl = query_exp_oacl | \
                                 Q("term", objectacls__entityId=group.id)
        query_exp = query_exp & query_exp_oacl
        ms = ms.add(Search(index='experiment')
                    .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                    .query(query_exp))

        query_dataset = Q("match", description=query_text)
        query_dataset = query_dataset | Q("match", tags=query_text)
        query_dataset_oacl = Q("term", objectacls__entityId=user.id) #| \Q("term", **{'experiment.public_access': 100})
        for group in groups:
            query_dataset_oacl = query_dataset_oacl | \
                                 Q("term", objectacls__entityId=group.id)
        query_dataset = query_dataset & query_dataset_oacl
        ms = ms.add(Search(index='dataset')
                    .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                    .query(query_dataset))

        query_datafile = Q("match", filename=query_text)
        query_datafile_oacl = Q("term", objectacls__entityId=user.id)
        for group in groups:
            query_datafile_oacl = query_datafile_oacl | \
                                  Q("term", objectacls__entityId=group.id)
        query_datafile = query_datafile & query_datafile_oacl
        ms = ms.add(Search(index='datafile')
                    .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                    .query(query_datafile))

        results = ms.execute()
        result_dict = {k: [] for k in ["projects", "experiments", "datasets", "datafiles"]}
        for item in results:
            for hit in item.hits.hits:

                sensitive_bool = False
                size = 0
                if not authz.has_access(request, hit["_source"]["id"], hit["_index"]):
                    continue

                if authz.has_sensitive_access(request, hit["_source"]["id"], hit["_index"]):
                    sensitive_bool = True

                size = authz.get_nested_size(request, hit["_source"]["id"], hit["_index"])

                safe_hit = hit.copy()
                safe_hit["_source"].pop("objectacls")
                safe_hit["_source"]["size"] = filesizeformat(size)

                if hit["_index"] != 'datafile':
                    safe_hit["_source"]["counts"] = authz.get_nested_count(request,
                                                        hit["_source"]["id"], hit["_index"])

                    safe_hit["_source"]["userDownloadRights"] = authz.get_nested_has_download(request,
                                                        hit["_source"]["id"], hit["_index"])

                else:
                    if authz.has_download_access(request, hit["_source"]["id"],
                                                 hit["_index"]):
                        safe_hit["_source"]["userDownloadRights"] = "full"
                    else:
                        safe_hit["_source"]["userDownloadRights"] = "none"

                if not sensitive_bool:
                    for idx, param in enumerate(hit["_source"]["parameters"]):
                        is_sensitive = authz.get_obj_parameter(param["full_name"],
                                                         hit["_source"]["id"],
                                                         hit["_index"])
                        if is_sensitive.sensitive_metadata:
                            safe_hit["_source"]["parameters"].pop(idx)

                result_dict[hit["_index"]+"s"].append(safe_hit)

        return [SearchObject(id=1, hits=result_dict)]

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


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
            safe_hit = hit.copy()
            safe_hit["_source"].pop("objectacls")
            result_dict[hit["_index"]+'s'].append(safe_hit)

    return result_dict
