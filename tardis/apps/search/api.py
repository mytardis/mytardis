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

from tardis.tardis_portal.models import Experiment, DataFile, Dataset
from tardis.tardis_portal.api import default_authentication

LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)
MAX_SEARCH_RESULTS = settings.MAX_SEARCH_RESULTS


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

    def get_object_list(self, request):
        user = request.user
        groups = user.groups.all()
        query_text = request.GET.get('query', None)
        index_list = ['experiments', 'dataset', 'datafile']
        ms = MultiSearch(index=index_list)
        query_exp = Q("match", title=query_text) & Q("term", objectacls__entityId=user.id)
        ms = ms.add(Search(index='experiments').extra(size=MAX_SEARCH_RESULTS).query(query_exp))
        query_dataset = Q("match", description=query_text)
        query_dataset_oacl = Q("term", **{'experiments.objectacls.entityId': user.id})
        ms = ms.add(Search(index='dataset').extra(size=MAX_SEARCH_RESULTS).query(query_dataset)
                    .query('nested', path='experiments', query=query_dataset_oacl))
        query_datafile = Q("match", filename=query_text)
        query_datafile_oacl = Q("term", **{'dataset.experiments.objectacls.entityId': user.id})
        ms = ms.add(Search(index='datafile').extra(size=MAX_SEARCH_RESULTS).query(query_datafile)
                    .query('nested', path='dataset.experiments', query=query_datafile_oacl))
        results = ms.execute()
        result_dict = {k: [] for k in ["experiments", "datasets", "datafiles"]}
        for item in results:
            for hit in item.hits.hits:
                if hit["_index"] == "dataset":
                    result_dict["datasets"].append(hit)

                elif hit["_index"] == "experiments":
                    result_dict["experiments"].append(hit)

                elif hit["_index"] == "datafile":
                    result_dict["datafiles"].append(hit)

        return [SearchObject(id=1, hits=result_dict)]

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


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

    def get_object_list(self, request):
        return request

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_create(self, bundle, **kwargs):
        bundle = self.dehydrate(bundle)
        return bundle

    def dehydrate(self, bundle):
        user = bundle.request.user
        groups = user.groups.all()
        # if anonymous user search public data only
        query_text = bundle.data.get("text", None)
        type_tag = bundle.data.get("TypeTag", None)
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
            end_date_utc = datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ")\
                .replace(tzinfo=pytz.timezone('UTC'))
            end_date = end_date_utc.astimezone(LOCAL_TZ).date()
        else:
            # set end date to today's date
            end_date = datetime.datetime.today().replace(tzinfo=pytz.timezone('UTC'))
        if start_date:
            start_date_utc = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ")\
                .replace(tzinfo=pytz.timezone('UTC'))
            start_date = start_date_utc.astimezone(LOCAL_TZ).date()
        instrument_list = bundle.data.get("InstrumentList", None)
        if instrument_list:
            instrument_list_string = ' '.join(instrument_list)
        # query for experiment model
        ms = MultiSearch(index=index_list)
        if 'experiments' in index_list:
            q = Q("match", title=query_text)
            if start_date is not None:
                q = q & Q("range", created_time={'gte': start_date, 'lte': end_date})
            ms = ms.add(Search(index='experiments').extra(size=MAX_SEARCH_RESULTS).query(q))
        if 'dataset' in index_list:
            q = Q("match", description=query_text)
            if start_date is not None:
                q = q & Q("range", created_time={'gte': start_date, 'lte': end_date})
            if instrument_list:
                q = q & Q("match", instrument__name=instrument_list_string)
            # add instrument query
            ms = ms.add(Search(index='dataset').extra(size=MAX_SEARCH_RESULTS).query(q))
        if 'datafile' in index_list:
            q = Q("match", filename=query_text)
            if start_date is not None:
                q = q & Q("range", created_time={'gte': start_date, 'lte': end_date})
            ms = ms.add(Search(index='datafile').extra(size=MAX_SEARCH_RESULTS).query(q))
        result = ms.execute()
        result_dict = {k: [] for k in ["experiments", "datasets", "datafiles"]}
        for item in result:
            for hit in item.hits.hits:
                if hit["_index"] == "dataset":
                    check_dataset_access = filter_dataset_result(hit,
                                                                 userid=user.id,
                                                                 groups=groups)
                    if check_dataset_access:
                        result_dict["datasets"].append(hit)

                elif hit["_index"] == "experiments":
                    check_experiment_access = filter_experiment_result(hit,
                                                                       userid=user.id,
                                                                       groups=groups)
                    if check_experiment_access:
                        result_dict["experiments"].append(hit)

                elif hit["_index"] == "datafile":
                    check_datafile_access = filter_datafile_result(hit,
                                                                   userid=user.id,
                                                                   groups=groups)
                    if check_datafile_access:
                        result_dict["datafiles"].append(hit)

        if bundle.request.method == 'POST':
            bundle.obj = SearchObject(id=1, hits=result_dict)
        return bundle


def filter_experiment_result(hit, userid, groups):
    exp = Experiment.objects.get(id=hit["_id"])
    if exp.public_access == 100:
        return True
    if exp.objectacls.filter(entityId=userid).count() > 0:
        return True
    for group in groups:
        if exp.objectacls.filter(entityId=group.id).count() > 0:
            return True
    return False


def filter_dataset_result(hit, userid, groups):
    dataset = Dataset.objects.get(id=hit["_id"])
    exps = dataset.experiments.all()
    for exp in exps:
        if exp.public_access == 100:
            return True
        if exp.objectacls.filter(entityId=userid).count() > 0:
            return True
        for group in groups:
            if exp.objectacls.filter(entityId=group.id).count() > 0:
                return True
    return False


def filter_datafile_result(hit, userid, groups):
    datafile = DataFile.objects.get(id=hit["_id"])
    ds = datafile.dataset
    exps = ds.experiments.all()
    for exp in exps:
        if exp.public_access == 100:
            return True
        if exp.objectacls.filter(entityId=userid).count() > 0:
            return True
        for group in groups:
            if exp.objectacls.filter(entityId=group.id).count() > 0:
                return True
    return False
