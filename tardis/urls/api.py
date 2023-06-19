"""
URLs for MyTardis's RESTful API
"""
import logging
from importlib import import_module

from django.conf import settings
from django.urls import include, re_path

from tastypie.api import Api
from tastypie.resources import Resource

from tardis.app_config import format_app_name_for_url, get_tardis_apps
from tardis.tardis_portal.api import (
    DatafileACLResource,
    DatafileParameterResource,
    DatafileParameterSetResource,
    DataFileResource,
    DatasetACLResource,
    DatasetParameterResource,
    DatasetParameterSetResource,
    DatasetResource,
    ExperimentACLResource,
    ExperimentAuthorResource,
    ExperimentParameterResource,
    ExperimentParameterSetResource,
    ExperimentResource,
    FacilityResource,
    GroupResource,
    InstrumentResource,
    IntrospectionResource,
    LocationResource,
    ParameterNameResource,
    ReplicaResource,
    SchemaResource,
    StorageBoxAttributeResource,
    StorageBoxOptionResource,
    StorageBoxResource,
    UserResource,
)

logger = logging.getLogger(__name__)

v1_api = Api(api_name="v1")
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
v1_api.register(IntrospectionResource())

for app_name, app in get_tardis_apps():
    try:
        if app_name == "projects":
            continue
        app_api = import_module("%s.api" % app)
        for res_name in dir(app_api):
            if not res_name.endswith("AppResource"):
                continue
            resource = getattr(app_api, res_name)
            if not issubclass(resource, Resource):
                continue
            resource_name = resource._meta.resource_name
            if not resource_name.startswith(app_name):
                resource._meta.resource_name = "%s_%s" % (
                    format_app_name_for_url(app_name),
                    resource_name,
                )
            v1_api.register(resource())
    except ImportError as e:
        logger.debug("App API URLs import error: %s" % str(e))

# Import project app urls here to avoid /apps prefix in url
if "tardis.apps.projects" in settings.INSTALLED_APPS:
    from tardis.apps.projects.api import (
        ProjectACLResource,
        ProjectParameterResource,
        ProjectParameterSetResource,
        ProjectResource,
    )

    v1_api.register(ProjectResource())
    v1_api.register(ProjectACLResource())
    v1_api.register(ProjectParameterSetResource())
    v1_api.register(ProjectParameterResource())


api_urls = [re_path(r"^", include(v1_api.urls))]

tastypie_swagger_urls = [
    re_path(
        r"v1/swagger/",
        include("tastypie_swagger.urls", namespace="api_v1_tastypie_swagger"),
        kwargs={
            "tastypie_api_module": v1_api,
            "namespace": "api_v1_tastypie_swagger",
            "version": "1",
        },
    ),
]
