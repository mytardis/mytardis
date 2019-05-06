'''
RESTful API for MyTardis search.
Implemented with Tastypie.

.. moduleauthor:: Manish Kumar <rishimanish123@gmail.com>
'''
import json
from django.conf import settings

from tastypie import fields
from tastypie.resources import Resource, Bundle
from tastypie.exceptions import BadRequest
from tastypie.serializers import Serializer
from django_elasticsearch_dsl.search import Search

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
    hits = fields.ApiField(attribute='hits')

    class Meta:
        resource_name = 'simple-search'
        list_allowed_methods = ['get', 'post']
        serializer = default_serializer
        authentication = default_authentication
        object_class = SearchObject

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

