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

from tardis.tardis_portal.api import default_authentication
from tardis.tardis_portal.models import Instrument

LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)
MAX_SEARCH_RESULTS = settings.MAX_SEARCH_RESULTS
MIN_CUTOFF_SCORE = settings.MIN_CUTOFF_SCORE


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
                    "datafiles": len(result_dict["datafiles"])
                },
                request=request
            )

    def get_object_list(self, request):
        user = request.user
        query_text = request.GET.get('query', None)
        if not user.is_authenticated:
            result_dict = simple_search_public_data(query_text)
            self.log_search_event(request, query_text, result_dict)
            return [SearchObject(id=1, hits=result_dict)]
        groups = user.groups.all()
        index_list = ['experiments', 'dataset', 'datafile']
        ms = MultiSearch(index=index_list)

        query_exp = Q("match", title=query_text)
        query_exp_oacl = Q("term", acls__entityId=user.id) | \
            Q("term", public_access=100)
        for group in groups:
            query_exp_oacl = query_exp_oacl | \
                                 Q("term", acls__entityId=group.id)
        query_exp = query_exp & query_exp_oacl
        ms = ms.add(Search(index='experiments')
                    .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                    .query(query_exp))

        query_dataset = Q("match", description=query_text)

        query_dataset_oacl = Q("term", **{'acls.entityId': user.id}) | \
            Q("term", **{'experiments.public_access': 100})
        for group in groups:
            query_dataset_oacl = query_dataset_oacl | \
                                 Q("term", **{'acls.entityId': group.id})
        ms = ms.add(Search(index='dataset')
                    .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE).query(query_dataset)
                    .query('nested', path='experiments', query=query_dataset_oacl))

        query_datafile = Q("match", filename=query_text)
        query_datafile_oacl = Q("term", acls__entityId=user.id) | \
            Q("term", experiments__public_access=100)
        for group in groups:
            query_datafile_oacl = query_datafile_oacl | \
                                 Q("term", acls__entityId=group.id)
        query_datafile = query_datafile & query_datafile_oacl
        ms = ms.add(Search(index='datafile')
                    .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE).query(query_datafile))
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
    index_list = ['experiments', 'dataset', 'datafile']
    ms = MultiSearch(index=index_list)
    query_exp = Q("match", title=query_text)
    query_exp_oacl = Q("term", public_access=100)
    query_exp = query_exp & query_exp_oacl
    ms = ms.add(Search(index='experiments')
                .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                .query(query_exp))
    query_dataset = Q("match", description=query_text)
    query_dataset_oacl = Q("term", **{'experiments.public_access': 100})
    ms = ms.add(Search(index='dataset')
                .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE).query(query_dataset)
                .query('nested', path='experiments', query=query_dataset_oacl))
    query_datafile = Q("match", filename=query_text)
    query_datafile_oacl = Q("term", experiments__public_access=100)
    query_datafile = query_datafile & query_datafile_oacl
    ms = ms.add(Search(index='datafile')
                .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                .query(query_datafile))
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
    hits = fields.ApiField(attribute='hits', null=True)

    class Meta:
        resource_name = 'advance-search'
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
        user = bundle.request.user
        groups = user.groups.all()

        # if anonymous user search public data only
        query_text = bundle.data.get("text", None)
        type_tag = bundle.data.get("TypeTag", [])
        index_list = []
        for type in type_tag:
            if type == 'Experiment':
                index_list.append('experiments')
            elif type == 'Dataset':
                index_list.append('dataset')
            elif type == 'Datafile':
                index_list.append('datafile')
        end_date = bundle.data.get("EndDate", None)
        start_date = bundle.data.get("StartDate", None)
        if end_date is not None:
            end_date_utc = datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ") \
                .replace(tzinfo=pytz.timezone('UTC'))
            end_date = end_date_utc.astimezone(LOCAL_TZ).date()
        else:
            # set end date to today's date
            end_date = datetime.datetime.today().replace(tzinfo=pytz.timezone('UTC'))
        if start_date:
            start_date_utc = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ") \
                .replace(tzinfo=pytz.timezone('UTC'))
            start_date = start_date_utc.astimezone(LOCAL_TZ).date()
        instrument_list = bundle.data.get("InstrumentList", None)
        instrument_list_id = []
        if instrument_list:
            for ins in instrument_list:
                instrument_list_id.append(Instrument.objects.get(name__exact=ins).id)
        # query for experiment model
        ms = MultiSearch(index=index_list)
        if 'experiments' in index_list:
            query_exp = Q("match", title=query_text)
            if user.is_authenticated:
                query_exp_oacl = Q("term", acls__entityId=user.id) | \
                                 Q("term", public_access=100)
                for group in groups:
                    query_exp_oacl = query_exp_oacl | \
                                     Q("term", acls__entityId=group.id)
            else:
                query_exp_oacl = Q("term", public_access=100)
            if start_date is not None:
                query_exp = query_exp & Q("range", created_time={'gte': start_date, 'lte': end_date})
            query_exp = query_exp & query_exp_oacl
            ms = ms.add(Search(index='experiments')
                        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                        .query(query_exp))
        if 'dataset' in index_list:
            query_dataset = Q("match", description=query_text)
            if user.is_authenticated:
                query_dataset_oacl = Q("term", **{'acls.entityId': user.id}) | \
                                     Q("term", **{'experiments.public_access': 100})
                for group in groups:
                    query_dataset_oacl = query_dataset_oacl | \
                                         Q("term", **{'acls.entityId': group.id})
            else:
                query_dataset_oacl = Q("term", **{'experiments.public_access': 100})
            if start_date is not None:
                query_dataset = query_dataset & Q("range", created_time={'gte': start_date, 'lte': end_date})
            if instrument_list:
                query_dataset = query_dataset & Q("terms", **{'instrument.id': instrument_list_id})
            # add instrument query
            ms = ms.add(Search(index='dataset')
                        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE).query(query_dataset)
                        .query('nested', path='experiments', query=query_dataset_oacl))
        if 'datafile' in index_list:
            query_datafile = Q("match", filename=query_text)
            if user.is_authenticated:
                query_datafile_oacl = Q("term", acls__entityId=user.id) | \
                                      Q("term", experiments__public_access=100)
                for group in groups:
                    query_datafile_oacl = query_datafile_oacl | \
                                          Q("term", acls__entityId=group.id)
            else:
                query_datafile_oacl = Q("term", experiments__public_access=100)
            if start_date is not None:
                query_datafile = query_datafile & Q("range", created_time={'gte': start_date, 'lte': end_date})
            query_datafile = query_datafile & query_datafile_oacl
            ms = ms.add(Search(index='datafile')
                        .extra(size=MAX_SEARCH_RESULTS, min_score=MIN_CUTOFF_SCORE)
                        .query(query_datafile))
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

        if bundle.request.method == 'POST':
            bundle.obj = SearchObject(id=1, hits=result_dict)
        return bundle
