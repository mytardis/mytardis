from django.contrib import admin
admin.autodiscover()

from django.contrib.auth.views import logout
from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from registration.backends.default.views import RegistrationView

from tardis.tardis_portal.forms import RegistrationForm

from django.http import HttpResponse

import django_jasmine.urls


def getTardisApps():
    return map(lambda app: app.split('.').pop(),
               filter(lambda app: app.startswith(settings.TARDIS_APP_ROOT),
                      settings.INSTALLED_APPS))

handler500 = 'tardis.views.error_handler'

rapidconnect_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^auth/jwt$', 'rcauth'),
)

core_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^$', 'index'),
    url(r'^site-settings.xml/$', 'site_settings', name='tardis-site-settings'),
    url(r'^mydata/$', 'my_data', name='mydata'),
    url(r'^public_data/', 'public_data', name='public_data'),
    (r'^about/$', 'about'),
    (r'^stats/$', 'stats'),
    (r'^help/$', 'user_guide'),
    (r'^robots\.txt$', lambda r: HttpResponse(
        "User-agent: *\nDisallow: /download/\nDisallow: /stats/",
        mimetype="text/plain"))
)

experiment_lists = patterns(
    'tardis.tardis_portal.views',
    url(r'^$', 'experiment_index'),
    url(r'^/mine$', 'experiment_list_mine',
        name="tardis_portal.experiment_list_mine"),
    url(r'^/public$', 'experiment_list_public',
        name="tardis_portal.experiment_list_public"),
    url(r'^/shared$', 'experiment_list_shared',
        name="tardis_portal.experiment_list_shared"),
    )

experiment_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^view/(?P<experiment_id>\d+)/$', 'view_experiment'),
    (r'^edit/(?P<experiment_id>\d+)/$', 'edit_experiment'),
    (r'^list', include(experiment_lists)),
    (r'^view/$', 'experiment_index'),  # Legacy URL
    (r'^search/$', 'search_experiment'),
    (r'^create/$', 'create_experiment'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/add/user/'
     '(?P<username>[\w\-][\w\-\.]+(@[\w\-][\w\-\.]+[a-zA-Z]{1,4})*)/$',
     'add_experiment_access_user'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/remove/user/'
     '(?P<username>[\w\.]+)/$', 'remove_experiment_access_user'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/change/user/'
     '(?P<username>[\w\.]+)/$', 'change_user_permissions'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/user/$',
     'retrieve_access_list_user'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/user/readonly/$',
     'retrieve_access_list_user_readonly'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/add/group/'
     '(?P<groupname>.+)/$', 'add_experiment_access_group'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/remove/group/'
     '(?P<group_id>\d+)/$', 'remove_experiment_access_group'),
    (r'^control_panel/create/group/$', 'create_group'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/change/group/'
     '(?P<group_id>\d+)/$', 'change_group_permissions'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/group/$',
     'retrieve_access_list_group'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/group/readonly/$',
     'retrieve_access_list_group_readonly'),
    (r'^control_panel/create/user/$', 'create_user'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/external/$',
     'retrieve_access_list_external'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/tokens/$',
     'retrieve_access_list_tokens'),
    (r'^control_panel/$', 'control_panel'),
    (r'^view/(?P<experiment_id>\d+)/create_token/$', 'create_token'),
    (r'^view/(?P<experiment_id>\d+)/rifcs/$', 'view_rifcs'),
    (r'^view/(?P<experiment_id>\d+)/public_access_badge/$',
     'experiment_public_access_badge'),
    (r'^(?P<experiment_id>\d+)/add-dataset$', 'add_dataset'),
    )

token_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^login/(?P<token>.+)/', 'token_login'),
    (r'^delete/(?P<token_id>.+)/', 'token_delete'),
    )


accounts_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^login/$', 'login'),
    (r'^manage$', 'manage_user_account'),
    (r'^manage_auth_methods/$', 'manage_auth_methods'),
    url(r'^register/$', RegistrationView.as_view(  # pylint: disable=E1120
        form_class=RegistrationForm),
        name='register'),
    (r'', include('registration.backends.default.urls')),
    )

dataset_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^(?P<dataset_id>\d+)/stage-files$', 'stage_files_to_dataset'),
    (r'^(?P<dataset_id>\d+)$', 'view_dataset'),
    (r'^(?P<dataset_id>\d+)/edit$', 'edit_dataset'),
    (r'^(?P<dataset_id>\d+)/thumbnail$', 'dataset_thumbnail'),
)
iiif_urls = patterns(
    'tardis.tardis_portal.iiif',
    url(r'^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/'
        r'(?P<rotation>[\d\.]+)/(?P<quality>\w+)$',
        'download_image'),
    url(r'^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/'
        r'(?P<rotation>[\d\.]+)/(?P<quality>\w+).(?P<format>\w+)$',
        'download_image'),
    url(r'^(?P<datafile_id>\d+)/info.(?P<format>\w+)$', 'download_info'),
    )

datafile_urls = patterns(
    '',
    (r'^search/$', 'tardis.tardis_portal.views.search_datafile'),
    url(r'^view/(?P<datafile_id>\d+)/$',
        'tardis.tardis_portal.download.view_datafile',
        name="view_datafile"),
    (r'^iiif/', include(iiif_urls)),
)

json_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^dataset/(?P<dataset_id>\d+)$', 'dataset_json'),
    (r'^experiment/(?P<experiment_id>\d+)/dataset/$',
     'experiment_datasets_json'),
    (r'^experiment/(?P<experiment_id>\d+)/dataset/(?P<dataset_id>\d+)$',
     'dataset_json'),
)

ajax_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^parameters/(?P<datafile_id>\d+)/$', 'retrieve_parameters'),
    (r'^datafile_details/(?P<datafile_id>\d+)/$',
     'display_datafile_details'),
    (r'^dataset_metadata/(?P<dataset_id>\d+)/$', 'retrieve_dataset_metadata'),
    (r'^experiment_metadata/(?P<experiment_id>\d+)/$',
        'retrieve_experiment_metadata'),
    (r'^datafile_list/(?P<dataset_id>\d+)/$', 'retrieve_datafile_list'),
    (r'^user_list/$', 'retrieve_user_list'),
    (r'^group_list/$', 'retrieve_group_list'),
    (r'^group_list_by_user/$', 'retrieve_group_list_by_user'),
    (r'^upload_complete/$', 'upload_complete'),
    (r'^upload_files/(?P<dataset_id>\d+)/$', 'upload_files'),
    (r'^import_staging_files/(?P<dataset_id>\d+)/$', 'import_staging_files'),
    (r'^list_staging_files/(?P<dataset_id>\d+)/$', 'list_staging_files'),
    (r'^experiment/(?P<experiment_id>\d+)/description$',
     'experiment_description'),
    (r'^experiment/(?P<experiment_id>\d+)/datasets$', 'experiment_datasets'),
    (r'^edit_datafile_parameters/(?P<parameterset_id>\d+)/$',
        'edit_datafile_par'),
    (r'^edit_dataset_parameters/(?P<parameterset_id>\d+)/$',
        'edit_dataset_par'),
    (r'^edit_experiment_parameters/(?P<parameterset_id>\d+)/$',
        'edit_experiment_par'),
    (r'^add_datafile_parameters/(?P<datafile_id>\d+)/$',
        'add_datafile_par'),
    (r'^add_dataset_parameters/(?P<dataset_id>\d+)/$',
        'add_dataset_par'),
    (r'^add_experiment_parameters/(?P<experiment_id>\d+)/$',
        'add_experiment_par'),
    (r'^parameter_field_list/$', 'retrieve_field_list'),
    (r'^experiment/(?P<experiment_id>\d+)/rights$', 'choose_rights'),
    (r'^experiment/(?P<experiment_id>\d+)/share$', 'share'),
    (r'^experiment/(?P<experiment_id>\d+)/dataset-transfer$',
     'experiment_dataset_transfer'),
    (r'^license/list$', 'retrieve_licenses'),
    (r'^json/', include(json_urls)),
    (r'^feedback/', 'feedback'),
)

download_urls = patterns(
    'tardis.tardis_portal.download',
    (r'^datafile/(?P<datafile_id>\d+)/$', 'download_datafile'),
    (r'^datafiles/$', 'streaming_download_datafiles'),
    (r'^experiment/(?P<experiment_id>\d+)/$',
     'streaming_download_experiment'),
    (r'^experiment/(?P<experiment_id>\d+)/'
     r'(?P<comptype>[a-z]{3})/$',  # tgz or tar
     'streaming_download_experiment'),
    (r'^experiment/(?P<experiment_id>\d+)/'
     r'(?P<comptype>[a-z]{3})/(?P<organization>[^/]+)/$',
     'streaming_download_experiment'),
    (r'^dataset/(?P<dataset_id>\d+)/$',
     'streaming_download_dataset'),
    (r'^dataset/(?P<dataset_id>\d+)/'
     r'(?P<comptype>[a-z]{3})/$',  # tgz or tar
     'streaming_download_dataset'),
    (r'^dataset/(?P<dataset_id>\d+)/'
     r'(?P<comptype>[a-z]{3})/(?P<organization>[^/]+)/$',
     'streaming_download_dataset'),
    (r'^api_key/$', 'download_api_key'),
    )

group_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^(?P<group_id>\d+)/$', 'retrieve_group_userlist'),
    (r'^(?P<group_id>\d+)/readonly$', 'retrieve_group_userlist_readonly'),
    (r'^(?P<group_id>\d+)/add/(?P<username>[\w\.]+)/$',
     'add_user_to_group'),
    (r'^(?P<group_id>\d+)/remove/(?P<username>[\w\.]+)/$',
     'remove_user_from_group'),
    )

facility_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^overview/$', 'facility_overview'),
    (r'^fetch_data/(?P<facility_id>\d+)/count/', 'fetch_facility_data_count'),
    (r'^fetch_data/(?P<facility_id>\d+)/'
     r'(?P<start_index>\d+)/(?P<end_index>\d+)/$',
     'fetch_facility_data'),
    (r'^fetch_facilities_list/$', 'fetch_facilities_list'),
    )

display_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^ExperimentImage/load/(?P<parameter_id>\d+)/$',
     'load_experiment_image'),
    (r'^DatasetImage/load/(?P<parameter_id>\d+)/$',
     'load_dataset_image'),
    (r'^DatafileImage/load/(?P<parameter_id>\d+)/$',
     'load_datafile_image'),
    (r'^ExperimentImage/(?P<experiment_id>\d+)/'
     '(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$',
     'display_experiment_image'),
    (r'^DatasetImage/(?P<dataset_id>\d+)/(?P<parameterset_id>\d+)/'
     '(?P<parameter_name>\w+)/$',
     'display_dataset_image'),
    (r'^DatafileImage/(?P<datafile_id>\d+)/'
     '(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$',
     'display_datafile_image'),
)

# # API SECTION
from tardis.tardis_portal.api import DatasetParameterSetResource
from tardis.tardis_portal.api import DatasetParameterResource
from tardis.tardis_portal.api import DatasetResource
from tardis.tardis_portal.api import DataFileResource
from tardis.tardis_portal.api import DatafileParameterSetResource
from tardis.tardis_portal.api import DatafileParameterResource
from tardis.tardis_portal.api import ExperimentParameterResource
from tardis.tardis_portal.api import ExperimentParameterSetResource
from tardis.tardis_portal.api import ExperimentResource
from tardis.tardis_portal.api import LocationResource
from tardis.tardis_portal.api import ParameterNameResource
from tardis.tardis_portal.api import ReplicaResource
from tardis.tardis_portal.api import SchemaResource
from tardis.tardis_portal.api import StorageBoxResource
from tardis.tardis_portal.api import UserResource
from tardis.tardis_portal.api import GroupResource
from tardis.tardis_portal.api import ObjectAclResource
from tardis.tardis_portal.api import UploaderResource
from tardis.tardis_portal.api import UploaderStagingHostResource
from tardis.tardis_portal.api import UploaderRegistrationRequestResource
from tardis.tardis_portal.api import FacilityResource
from tardis.tardis_portal.api import InstrumentResource
from tastypie.api import Api
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
v1_api.register(UserResource())
v1_api.register(GroupResource())
v1_api.register(ObjectAclResource())
v1_api.register(UploaderResource())
v1_api.register(UploaderStagingHostResource())
v1_api.register(UploaderRegistrationRequestResource())
v1_api.register(FacilityResource())
v1_api.register(InstrumentResource())
api_urls = patterns(
    '',
    (r'^', include(v1_api.urls)),
)
# # END API SECTION

apppatterns = patterns('',)
for app in getTardisApps():
    apppatterns += patterns('tardis.apps',
                            (r'^%s/' % app.replace('_', '-'),
                             include('%s.%s.urls' %
                                     (settings.TARDIS_APP_ROOT, app))))
urlpatterns = patterns(
    # (r'^search/quick/$', 'tardis.tardis_portal.views.search_quick'),
    '',
    (r'', include(core_urls)),
    # API views
    (r'^api/', include(api_urls)),

    # Experiment Views
    (r'^experiment/', include(experiment_urls)),

    # Dataset Views
    (r'^dataset/', include(dataset_urls)),

    # Datafile Views
    (r'^datafile/', include(datafile_urls)),

    # Download Views
    (r'^download/', include(download_urls)),

    # Ajax Views
    (r'^ajax/', include(ajax_urls)),

    # Account Views
    (r'^accounts/', include(accounts_urls)),

    # Group Views
    (r'^groups/$', 'tardis.tardis_portal.views.manage_groups'),
    (r'^group/', include(group_urls)),

    # Facility views
    (r'^facility/', include(facility_urls)),

    # Display Views
    (r'^display/', include(display_urls)),

    # Login/out
    (r'^login/$', 'tardis.tardis_portal.views.login'),
    (r'^logout/$', logout, {'next_page': '/'}),

    # Rapid Connect
    (r'^rc/', include(rapidconnect_urls)),

    # Admin
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^upload/(?P<dataset_id>\d+)/$', 'tardis.tardis_portal.views.upload'),

    # Search
    (r'^search/$', 'tardis.tardis_portal.views.single_search'),

    # Apps
    (r'^apps/', include(apppatterns)),

    # Token login
    (r'^token/', include(token_urls)),

    # Jasmine JavaScript Tests
    (r'^jasmine/', include(django_jasmine.urls)),

)

# Handle static files from /static
urlpatterns += staticfiles_urlpatterns()

# Show compiled documentation to developers. Production instances can be
# enabled to show on readthedocs.org
if settings.DEBUG:
    from os import path
    urlpatterns += patterns(
        '',
        url(r'^docs/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': path.abspath(
                path.join(path.dirname(__file__), '..', "docs/html/")),
            }),
    )
