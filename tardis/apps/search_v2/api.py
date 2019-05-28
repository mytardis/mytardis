'''
RESTful API for MyTardis search.
Implemented with Tastypie.

.. moduleauthor:: Manish Kumar <rishimanish123@gmail.com>
'''
import json
import datetime
from django.conf import settings

from tastypie import fields
from tastypie.resources import Resource, Bundle
from tastypie.exceptions import BadRequest
from tastypie.serializers import Serializer
from django_elasticsearch_dsl.search import Search
from elasticsearch_dsl import MultiSearch, Q

from tardis.tardis_portal.api import default_authentication


class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
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
        list_allowed_methods = ['get', 'post']
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

    def get_object_list(self, bundle):
        query_text = bundle.request.GET.get('query', None)
        if not query_text:
            raise BadRequest("Missing query parameter")
        s = Search()
        s = s[0:20]
        search = s.query(
            "multi_match",
            query=query_text,
            fields=["title", "description", "filename"]
        )
        results = search.execute()
        result_dict = {k: [] for k in ["experiments", "datasets", "datafiles"]}
        for hit in results.hits.hits:
            if hit["_index"] == "dataset":
                result_dict["datasets"].append(hit)
            elif hit["_index"] == "experiments":
                result_dict["experiments"].append(hit)
            elif hit["_index"] == "datafile":
                result_dict["datafiles"].append(hit)

        return [SearchObject(id=1, hits=result_dict)]

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle)


class AdvanceSearchAppResource(Resource):
    hits = fields.ApiField(attribute='hits', null=True)

    class Meta:
        resource_name = 'advance-search'
        list_allowed_methods = ['get', 'post']
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

    def get_object_list(self, bundle):
        return bundle

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle)

    def obj_create(self, bundle, **kwargs):
        bundle = self.dehydrate(bundle)
        return bundle

    def dehydrate(self, bundle):
        query_text = bundle.data["text"]
        type_tag = bundle.data["TypeTag"]
        index_list = []
        for type in type_tag:
            if type == 'Experiment':
                index_list.append('experiments')
            elif type == 'Dataset':
                index_list.append('dataset')
            elif type == 'Datafile':
                index_list.append('datafile')
        end_date = datetime.datetime.strptime(bundle.data["EndDate"], "%Y-%m-%dT%H:%M:%S.%fZ")
        start_date = datetime.datetime.strptime(bundle.data["StartDate"], "%Y-%m-%dT%H:%M:%S.%fZ")
        instrument_list = bundle.data["InstrumentList"]
        # query for experiment model
        ms = MultiSearch(index=index_list)
        if 'experiments' in index_list:
            q = Q("match", title=query_text) & Q("range", created_time={'gte': start_date, 'lt': end_date})
            ms = ms.add(Search().query(q))
        if 'dataset' in index_list:
            q = Q("match", description=query_text) & Q("range", created_time={'gte': start_date, 'lt': end_date})
            # add instrument query
            ms = ms.add(Search().query(q))
        if 'datafile' in index_list:
            q = Q("match", filename=query_text) & Q("range", created_time={'gte': start_date, 'lt': end_date})
            ms = ms.add(Search().query(q))
        result = ms.execute()
        result_dict = {k: [] for k in ["experiments", "datasets", "datafiles"]}
        for item in result:
            for hit in item.hits.hits:
                if hit["_index"] == "dataset":
                    result_dict["datasets"].append(hit)
                elif hit["_index"] == "experiments":
                    result_dict["experiments"].append(hit)
                elif hit["_index"] == "datafile":
                    result_dict["datafiles"].append(hit)

        if bundle.request.method == 'POST':
            bundle.obj = SearchObject(id=1, hits=result_dict)
        return bundle
