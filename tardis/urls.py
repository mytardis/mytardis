from importlib import import_module
import logging
from os import path

from django.contrib import admin

from django.contrib.auth.views import login
from django.contrib.auth.views import logout
from django.conf.urls import include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse

from registration.backends.default.views import RegistrationView

from tastypie.api import Api
from tastypie.resources import Resource

from tardis.app_config import get_tardis_apps
from tardis.app_config import format_app_name_for_url
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
    FacilityResource,
    GroupResource,
    InstrumentResource,
    LocationResource,
    ObjectACLResource,
    ParameterNameResource,
    ReplicaResource,
    SchemaResource,
    StorageBoxAttributeResource,
    StorageBoxOptionResource,
    StorageBoxResource,
    UserResource,
)
from tardis.tardis_portal.views import IndexView, ExperimentView, DatasetView
from tardis.tardis_portal.views.pages import site_routed_view
from tardis.tardis_portal.views import manage_groups
from tardis.tardis_portal.views import upload

admin.autodiscover()

logger = logging.getLogger(__name__)

handler500 = 'tardis.views.error_handler'

from tardis.tardis_portal.views import rcauth
rapidconnect_urls = [
    url (r'^auth/jwt$', rcauth),
]

overridable_urls = [
    url(r'^$', site_routed_view, {'_default_view': IndexView.as_view(),
                                  '_site_mappings':
                                      getattr(settings, 'INDEX_VIEWS', {})},
        name='index')
]

from tardis.tardis_portal.views import (
    site_settings,
    my_data,
    public_data,
    about,
    stats,
    user_guide,
    cybderduck_connection_window,
    sftp_access
)

core_urls = [
    url(r'^site-settings.xml/$', site_settings, name='tardis-site-settings'),
    url(r'^mydata/$', my_data, name='tardis.tardis_portal.views.my_data'),
    url(r'^public_data/', public_data,
        name='tardis.tardis_portal.views.public_data'),
    url(r'^about/$', about, name='tardis.tardis_portal.views.about'),
    url(r'^stats/$', stats, name='tardis.tardis_portal.views.stats'),
    url(r'^sftp_access/cyberduck/connection.png$',
        cybderduck_connection_window, name='cyberduck_connection_window'),
    url(r'^sftp_access/$', sftp_access,
        name='tardis.tardis_portal.views.sftp_access'),
    url(r'^robots\.txt$', lambda r: HttpResponse(
        "User-agent: *\nDisallow: /download/\nDisallow: /stats/",
        content_type="text/plain"))
]

from tardis.tardis_portal.views import (
    experiment_index,
    experiment_list_mine,
    experiment_list_public,
    experiment_list_shared
)
experiment_lists = [
    url(r'^$', experiment_index,
        name='tardis.tardis_portal.views.experiment_index'),
    url(r'^mine$', experiment_list_mine,
        name='tardis.tardis_portal.views.experiment_list_mine'),
    url(r'^public$', experiment_list_public,
        name='tardis.tardis_portal.views.experiment_list_public'),
    url(r'^shared$', experiment_list_shared,
        name='tardis.tardis_portal.views.experiment_list_shared'),
]

user_pattern = '[\w\-][\w\-\.]+(@[\w\-][\w\-\.]+[a-zA-Z]{1,4})*'
from tardis.tardis_portal.views import (
    edit_experiment,
    experiment_index,
    create_experiment,
    add_experiment_access_user,
    remove_experiment_access_user,
    change_user_permissions,
    retrieve_access_list_user,
    retrieve_access_list_user_readonly,
    add_experiment_access_group,
    remove_experiment_access_group,
    change_group_permissions,
    retrieve_access_list_group,
    retrieve_access_list_group_readonly,
    create_user,
    create_group,
    retrieve_access_list_external,
    retrieve_access_list_tokens,
    control_panel,
    create_token,
    view_rifcs,
    experiment_public_access_badge,
    add_dataset
)
experiment_urls = [
    url(r'^view/(?P<experiment_id>\d+)/$', ExperimentView.as_view(),
        name='tardis_portal.view_experiment'),
    url(r'^edit/(?P<experiment_id>\d+)/$', edit_experiment,
        name='tardis.tardis_portal.views.edit_experiment'),
    url(r'^list/', include(experiment_lists)),
    url(r'^view/$', experiment_index,  # Legacy URL
        name='tardis.tardis_portal.views.experiment_index'),
    url(r'^create/$', create_experiment,
        name='tardis.tardis_portal.views.create_experiment'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/add/user/'
        '(?P<username>%s)/$' % user_pattern,
        add_experiment_access_user,
        name='tardis.tardis_portal.views.add_experiment_access_user'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/remove/user/'
        '(?P<username>%s)/$' % user_pattern, remove_experiment_access_user,
        name='tardis.tardis_portal.views.remove_experiment_access_user'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/change/user/'
        '(?P<username>%s)/$' % user_pattern, change_user_permissions,
        name='tardis.tardis_portal.views.change_user_permissions'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/user/$',
        retrieve_access_list_user,
        name='tardis.tardis_portal.views.retrieve_access_list_user'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/user/readonly/$',
        retrieve_access_list_user_readonly,
        name='tardis.tardis_portal.views.retrieve_access_list_user_readonly'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/add/group/'
        '(?P<groupname>.+)/$', add_experiment_access_group,
        name='tardis.tardis_portal.views.add_experiment_access_group'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/remove/group/'
        '(?P<group_id>\d+)/$', remove_experiment_access_group,
        name='tardis.tardis_portal.views.remove_experiment_access_group'),
    url(r'^control_panel/create/group/$', create_group,
        name='tardis.tardis_portal.views.create_group'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/change/group/'
        '(?P<group_id>\d+)/$', change_group_permissions,
        name='tardis.tardis_portal.views.change_group_permissions'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/group/$',
        retrieve_access_list_group,
        name='tardis.tardis_portal.views.retrieve_access_list_group'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/group/readonly/$',
        retrieve_access_list_group_readonly,
        name='tardis.tardis_portal.views.retrieve_access_list_group_readonly'),
    url(r'^control_panel/create/user/$', create_user,
        name='tardis.tardis_portal.views.create_user'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/external/$',
        retrieve_access_list_external,
        name='tardis.tardis_portal.views.retrieve_access_list_external'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/tokens/$',
        retrieve_access_list_tokens,
        name='tardis.tardis_portal.views.retrieve_access_list_tokens'),
    url(r'^control_panel/$', control_panel,
        name='tardis.tardis_portal.views.control_panel'),
    url(r'^view/(?P<experiment_id>\d+)/create_token/$', create_token,
        name='tardis.tardis_portal.views.create_token'),
    url(r'^view/(?P<experiment_id>\d+)/rifcs/$', view_rifcs,
        name='tardis.tardis_portal.views.control_panel.view_rifcs'),
    url(r'^view/(?P<experiment_id>\d+)/public_access_badge/$',
        experiment_public_access_badge,
        name='tardis.tardis_portal.views.control_panel.experiment_public_access_badge'),
    url(r'^(?P<experiment_id>\d+)/add-dataset$', add_dataset,
        name='tardis.tardis_portal.views.add_dataset'),
]

from tardis.tardis_portal.views import (
    token_login,
    token_delete
)
token_urls = [
    url(r'^login/(?P<token>.+)/', token_login),
    url(r'^delete/(?P<token_id>.+)/', token_delete),
]


from tardis.tardis_portal.views import (
    login,
    manage_user_account,
    manage_auth_methods
)

accounts_urls = [
    url(r'^login/$', login, name='tardis.tardis_portal.views.login'),
    url(r'^manage$', manage_user_account,
        name='tardis.tardis_portal.views.manage_user_account'),
    url(r'^manage_auth_methods/$', manage_auth_methods,
        name='tardis.tardis_portal.views.manage_auth_methods'),
    url(r'^register/$', RegistrationView.as_view(),  # pylint: disable=E1120
        name='tardis.tardis_portal.views.register'),
    url(r'', include('registration.backends.default.urls')),
]


from tardis.tardis_portal.views import (
    stage_files_to_dataset,
    edit_dataset,
    dataset_thumbnail,
    checksums_download
)
dataset_urls = [
    url(r'^(?P<dataset_id>\d+)/stage-files$', stage_files_to_dataset,
        name='tardis.tardis_portal.views.stage_files_to_dataset'),
    url(r'^(?P<dataset_id>\d+)$', DatasetView.as_view(),
        name='tardis_portal.view_dataset'),
    url(r'^(?P<dataset_id>\d+)/edit$', edit_dataset,
        name='tardis.tardis_portal.views.edit_dataset'),
    url(r'^(?P<dataset_id>\d+)/thumbnail$', dataset_thumbnail,
        name='tardis.tardis_portal.views.dataset_thumbnail'),
    url(r'^(?P<dataset_id>\d+)/checksums$', checksums_download,
        name='tardis_portal.dataset_checksums'),
]

from tardis.tardis_portal.iiif import (
    download_image,
    download_info
)
iiif_urls = [
    url(r'^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/'
        r'(?P<rotation>[\d\.]+)/(?P<quality>\w+)$',
        download_image),
    url(r'^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/'
        r'(?P<rotation>[\d\.]+)/(?P<quality>\w+).(?P<format>\w+)$',
        download_image),
    url(r'^(?P<datafile_id>\d+)/info.(?P<format>\w+)$', download_info),
]

from tardis.tardis_portal.download import (
    view_datafile
)
datafile_urls = [
    url(r'^view/(?P<datafile_id>\d+)/$',
        view_datafile,
        name='view_datafile'),
    url(r'^iiif/', include(iiif_urls)),
]

from tardis.tardis_portal.views import (
    dataset_json,
    experiment_datasets_json
)
json_urls = [
    url(r'^dataset/(?P<dataset_id>\d+)$', dataset_json,
        name='tardis.tardis_portal.views.dataset_json'),
    url(r'^experiment/(?P<experiment_id>\d+)/dataset/$',
        experiment_datasets_json,
        name='tardis.tardis_portal.views.experiment_datasets_json'),
    url(r'^experiment/(?P<experiment_id>\d+)/dataset/(?P<dataset_id>\d+)$',
        dataset_json,
        name='tardis.tardis_portal.views.dataset_json'),
]

from tardis.tardis_portal.views import (
    retrieve_parameters,
    display_datafile_details,
    retrieve_experiment_metadata,
    retrieve_dataset_metadata,
    retrieve_datafile_list,
    cache_dataset,
    retrieve_user_list,
    retrieve_group_list,
    retrieve_group_list_by_user,
    upload_complete,
    upload_files,
    import_staging_files,
    list_staging_files,
    experiment_description,
    experiment_datasets,
    retrieve_owned_exps_list,
    retrieve_shared_exps_list,
    edit_datafile_par,
    edit_dataset_par,
    edit_experiment_par,
    add_datafile_par,
    add_dataset_par,
    add_experiment_par,
    choose_rights,
    share,
    experiment_dataset_transfer,
    retrieve_licenses,
    feedback
)
ajax_urls = [
    url(r'^parameters/(?P<datafile_id>\d+)/$', retrieve_parameters),
    url(r'^datafile_details/(?P<datafile_id>\d+)/$',
        display_datafile_details),
    url(r'^dataset_metadata/(?P<dataset_id>\d+)/$', retrieve_dataset_metadata,
        name='tardis.tardis_portal.views.retrieve_dataset_metadata'),
    url(r'^experiment_metadata/(?P<experiment_id>\d+)/$',
        retrieve_experiment_metadata,
        name='tardis.tardis_portal.views.retrieve_experiment_metadata'),
    url(r'^datafile_list/(?P<dataset_id>\d+)/$', retrieve_datafile_list,
        name='tardis.tardis_portal.views.retrieve_datafile_list'),
    url(r'^cache_dataset/(?P<dataset_id>\d+)/$', cache_dataset,
        name='cache_dataset'),
    url(r'^user_list/$', retrieve_user_list),
    url(r'^group_list/$', retrieve_group_list),
    url(r'^group_list_by_user/$', retrieve_group_list_by_user),
    url(r'^upload_complete/$', upload_complete),
    url(r'^upload_files/(?P<dataset_id>\d+)/$', upload_files),
    url(r'^import_staging_files/(?P<dataset_id>\d+)/$', import_staging_files),
    url(r'^list_staging_files/(?P<dataset_id>\d+)/$', list_staging_files),
    url(r'^experiment/(?P<experiment_id>\d+)/description$',
        experiment_description),
    url(r'^experiment/(?P<experiment_id>\d+)/datasets$', experiment_datasets),
    url(r'^owned_exps_list/$', retrieve_owned_exps_list,
        name='tardis.tardis_portal.views.retrieve_owned_exps_list'),
    url(r'^shared_exps_list/$', retrieve_shared_exps_list,
        name='tardis.tardis_portal.views.retrieve_shared_exps_list'),
    url(r'^edit_datafile_parameters/(?P<parameterset_id>\d+)/$',
        edit_datafile_par,
        name='tardis.tardis_portal.views.edit_datafile_par'),
    url(r'^edit_dataset_parameters/(?P<parameterset_id>\d+)/$',
        edit_dataset_par,
        name='tardis.tardis_portal.views.edit_dataset_par'),
    url(r'^edit_experiment_parameters/(?P<parameterset_id>\d+)/$',
        edit_experiment_par,
        name='tardis.tardis_portal.views.edit_experiment_par'),
    url(r'^add_datafile_parameters/(?P<datafile_id>\d+)/$',
        add_datafile_par,
        name='tardis.tardis_portal.views.add_datafile_par'),
    url(r'^add_dataset_parameters/(?P<dataset_id>\d+)/$',
        add_dataset_par,
        name='tardis.tardis_portal.views.add_dataset_par'),
    url(r'^add_experiment_parameters/(?P<experiment_id>\d+)/$',
        add_experiment_par,
        name='tardis.tardis_portal.views.add_experiment_par'),
    url(r'^experiment/(?P<experiment_id>\d+)/rights$', choose_rights,
        name='tardis.tardis_portal.views.choose_rights'),
    url(r'^experiment/(?P<experiment_id>\d+)/share$', share,
        name='tardis.tardis_portal.views.share'),
    url(r'^experiment/(?P<experiment_id>\d+)/dataset-transfer$',
        experiment_dataset_transfer,
        name='tardis.tardis_portal.views.experiment_dataset_transfer'),
    url(r'^license/list$', retrieve_licenses,
        name='tardis.tardis_portal.views.retrieve_licenses'),
    url(r'^json/', include(json_urls)),
    url(r'^feedback/', feedback,
        name='tardis.tardis_portal.views.feedback'),
]

from tardis.tardis_portal.download import (
    download_datafile,
    streaming_download_datafiles,
    streaming_download_experiment,
    streaming_download_dataset,
    download_api_key
)
download_urls = [
    url(r'^datafile/(?P<datafile_id>\d+)/$', download_datafile),
    url(r'^datafiles/$', streaming_download_datafiles),
    url(r'^experiment/(?P<experiment_id>\d+)/$',
        streaming_download_experiment,
        name='tardis.tardis_portal.download.streaming_download_experiment'),
    url(r'^experiment/(?P<experiment_id>\d+)/'
        r'(?P<comptype>[a-z]{3})/$',  # tgz or tar
        streaming_download_experiment,
        name='tardis.tardis_portal.download.streaming_download_experiment'),
    url(r'^experiment/(?P<experiment_id>\d+)/'
        r'(?P<comptype>[a-z]{3})/(?P<organization>[^/]+)/$',
     streaming_download_experiment),
    url(r'^dataset/(?P<dataset_id>\d+)/$',
        streaming_download_dataset,
        name='tardis.tardis_portal.download.streaming_download_dataset'),
    url(r'^dataset/(?P<dataset_id>\d+)/'
        r'(?P<comptype>[a-z]{3})/$',  # tgz or tar
        streaming_download_dataset,
        name='tardis.tardis_portal.download.streaming_download_dataset'),
    url(r'^dataset/(?P<dataset_id>\d+)/'
        r'(?P<comptype>[a-z]{3})/(?P<organization>[^/]+)/$',
        streaming_download_dataset,
        name='tardis.tardis_portal.download.streaming_download_dataset'),
    url(r'^api_key/$', download_api_key, name='download_api_key'),
]

from tardis.tardis_portal.views import (
    retrieve_group_userlist,
    retrieve_group_userlist_readonly,
    add_user_to_group,
    remove_user_from_group
)
group_urls = [
    url(r'^(?P<group_id>\d+)/$', retrieve_group_userlist,
        name='tardis.tardis_portal.views.retrieve_group_userlist'),
    url(r'^(?P<group_id>\d+)/readonly$', retrieve_group_userlist_readonly,
        name='tardis.tardis_portal.views.retrieve_group_userlist_readonly'),
    url(r'^(?P<group_id>\d+)/add/(?P<username>[\w\.]+)/$',
        add_user_to_group,
        name='tardis.tardis_portal.views.add_user_to_group'),
    url(r'^(?P<group_id>\d+)/remove/(?P<username>[\w\.]+)/$',
        remove_user_from_group,
        name='tardis.tardis_portal.views.remove_user_from_group'),
]

from tardis.tardis_portal.views import (
    facility_overview,
    facility_overview_data_count,
    facility_overview_experiments,
    facility_overview_dataset_detail,
    facility_overview_facilities_list
)
facility_urls = [
    url(r'^overview/$', facility_overview),
    url(r'^fetch_data/(?P<facility_id>\d+)/count/', facility_overview_data_count),
    url(r'^fetch_data/(?P<facility_id>\d+)/'
        r'(?P<start_index>\d+)/(?P<end_index>\d+)/$',
        facility_overview_experiments),
    url(r'^fetch_datafiles/(?P<dataset_id>\d+)/$',
        facility_overview_dataset_detail),
    url(r'^fetch_facilities_list/$', facility_overview_facilities_list),
]

from tardis.tardis_portal.views import (
    load_experiment_image,
    load_dataset_image,
    load_datafile_image,
    display_experiment_image,
    display_dataset_image,
    display_datafile_image
)
display_urls = [
    url(r'^ExperimentImage/load/(?P<parameter_id>\d+)/$',
        load_experiment_image,
        name='tardis.tardis_portal.views.load_experiment_image'),
    url(r'^DatasetImage/load/(?P<parameter_id>\d+)/$',
        load_dataset_image,
        name='tardis.tardis_portal.views.load_dataset_image'),
    url(r'^DatafileImage/load/(?P<parameter_id>\d+)/$',
        load_datafile_image,
        name='tardis.tardis_portal.views.load_datafile_image'),
    url(r'^ExperimentImage/(?P<experiment_id>\d+)/'
        '(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$',
        display_experiment_image,
        name='tardis.tardis_portal.views.display_experiment_image'),
    url(r'^DatasetImage/(?P<dataset_id>\d+)/(?P<parameterset_id>\d+)/'
        '(?P<parameter_name>\w+)/$',
        display_dataset_image,
        name='tardis.tardis_portal.views.display_dataset_image'),
    url(r'^DatafileImage/(?P<datafile_id>\d+)/'
        '(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$',
        display_datafile_image,
        name='tardis.tardis_portal.views.display_datafile_image'),
]

# # API SECTION
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
v1_api.register(LocationResource())
v1_api.register(ParameterNameResource())
v1_api.register(ReplicaResource())
v1_api.register(SchemaResource())
v1_api.register(StorageBoxResource())
v1_api.register(StorageBoxOptionResource())
v1_api.register(StorageBoxAttributeResource())
v1_api.register(UserResource())
v1_api.register(GroupResource())
v1_api.register(ObjectACLResource())
v1_api.register(FacilityResource())
v1_api.register(InstrumentResource())

# App API additions
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

api_urls = [
    url(r'^', include(v1_api.urls)),
]

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

# # END API SECTION

app_urls = []
for app_name, app in get_tardis_apps():
    app_urls += [
        url(r'^%s/' % format_app_name_for_url(app_name),
            include('%s.urls' % app))
    ]

urlpatterns = [
    url(r'', include(core_urls)),

    # API views
    url(r'^api/', include(api_urls)),

    # tastypie_swagger endpoints for API auto-documentation
    url(r'^api/', include(tastypie_swagger_urls)),

    # Experiment Views
    url(r'^experiment/', include(experiment_urls)),

    # Dataset Views
    url(r'^dataset/', include(dataset_urls)),

    # Datafile Views
    url(r'^datafile/', include(datafile_urls)),

    # Download Views
    url(r'^download/', include(download_urls)),

    # Ajax Views
    url(r'^ajax/', include(ajax_urls)),

    # Account Views
    url(r'^accounts/', include(accounts_urls)),

    # Group Views
    url(r'^groups/$', manage_groups,
        name='tardis.tardis_portal.views.manage_groups'),
    url(r'^group/', include(group_urls)),

    # Facility views
    url(r'^facility/', include(facility_urls)),

    # Display Views
    url(r'^display/', include(display_urls)),

    # Login/out
    url(r'^login/$', login),
    url(r'^logout/$', logout, {'next_page': '/'}, name='logout'),

    # Rapid Connect
    url(r'^rc/', include(rapidconnect_urls)),

    # Admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^upload/(?P<dataset_id>\d+)/$', upload),

    # Search
    url(r'^search/', include('tardis.search.urls')),

    # Apps
    url(r'^apps/', include(app_urls)),

    # Token login
    url(r'^token/', include(token_urls)),

    # Class-based views that may be overriden by apps
    url(r'', include(overridable_urls)),
]

# Handle static files from /static
urlpatterns += staticfiles_urlpatterns()

# Show compiled documentation to developers. Production instances can be
# enabled to show on readthedocs.org
if settings.DEBUG:
    from django.views.static import serve
    urlpatterns += [
        url(r'^docs/(?P<path>.*)$', serve, {
            'document_root': path.abspath(
                path.join(path.dirname(__file__), '..', "docs/html/")),
            }),
    ]
