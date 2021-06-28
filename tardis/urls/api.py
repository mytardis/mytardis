'''
URLs for MyTardis's RESTful API
'''
from importlib import import_module
import logging

from django.conf.urls import include, url

from tastypie.api import Api
from tastypie.resources import Resource

from tardis.app_config import format_app_name_for_url
from tardis.app_config import get_tardis_apps
from tardis.tardis_portal.api import (
    DatafileParameterResource,
    DatafileParameterSetResource,
    DataFileResource,
    DatasetParameterResource,
    DatasetParameterSetResource,
    DatasetResource,
    ExperimentParameterResource,
    ExperimentParameterSetResource,
    ExperimentResource,
    ExperimentAuthorResource,
    FacilityResource,
    GroupResource,
    InstrumentResource,
    LocationResource,
    ExperimentACLResource,
    DatasetACLResource,
    DatafileACLResource,
    ParameterNameResource,
    ReplicaResource,
    SchemaResource,
    StorageBoxAttributeResource,
    StorageBoxOptionResource,
    StorageBoxResource,
    UserResource,
)

logger = logging.getLogger(__name__)

v1_api = Api(api_name='v1')
v1_api.register(DatasetParameterSetResource())
v1_api.register(DatasetParameterResource())
v1_api.register(DatasetResource())
v1_api.register(DataFileResource())
v1_api.register(DatafileParameterSetResource())
v1_api.register(DatafileParameterResource())
v1_api.register(ExperimentParameterResource())
v1_api.register(ExperimentParameterSetResource())
v1_api.register(ExperimentResource())
v1_api.register(ExperimentAuthorResource())
v1_api.register(LocationResource())
v1_api.register(ParameterNameResource())
v1_api.register(ReplicaResource())
v1_api.register(SchemaResource())
v1_api.register(StorageBoxResource())
v1_api.register(StorageBoxOptionResource())
v1_api.register(StorageBoxAttributeResource())
v1_api.register(UserResource())
v1_api.register(GroupResource())
v1_api.register(ExperimentACLResource())
v1_api.register(DatasetACLResource())
v1_api.register(DatafileACLResource())
v1_api.register(FacilityResource())
v1_api.register(InstrumentResource())

for app_name, app in get_tardis_apps():
    try:
        app_api = import_module('%s.api' % app)
        for res_name in dir(app_api):
            if not res_name.endswith('AppResource'):
                continue
            resource = getattr(app_api, res_name)
            if not issubclass(resource, Resource):
                continue
            resource_name = resource._meta.resource_name
            if not resource_name.startswith(app_name):
                resource._meta.resource_name = '%s_%s' % (
                    format_app_name_for_url(app_name), resource_name)
            v1_api.register(resource())
    except ImportError as e:
        logger.debug('App API URLs import error: %s' % str(e))


api_urls = [ url(r'^', include(v1_api.urls)) ]

tastypie_swagger_urls = [
    url(r'v1/swagger/',
        include('tastypie_swagger.urls',
                namespace='api_v1_tastypie_swagger'),
        kwargs={
          "tastypie_api_module": v1_api,
          "namespace": "api_v1_tastypie_swagger",
          "version": "1"}
        ),
]
