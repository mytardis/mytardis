from django.contrib import admin
admin.autodiscover()
from django.contrib.auth.views import logout
from django.conf.urls.defaults import patterns, include
from django.conf import settings

from registration.views import register

from tardis.tardis_portal.forms import RegistrationForm

core_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^$', 'index'),
    (r'^site-settings.xml/$', 'site_settings'),
    (r'^about/$', 'about'),
    (r'^partners/$', 'partners'),
    (r'^stats/$', 'stats'),
    (r'^import_params/$', 'import_params'),
)

experiment_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^view/(?P<experiment_id>\d+)/$', 'view_experiment'),
    (r'^edit/(?P<experiment_id>\d+)/$', 'edit_experiment'),
    (r'^view/$', 'experiment_index'),
    (r'^search/$', 'search_experiment'),
    (r'^register/$', 'register_experiment_ws_xmldata'),
    (r'^register/internal/$', 'register_experiment_ws_xmldata_internal'),
    (r'^view/(?P<experiment_id>\d+)/publish/$', 'publish_experiment'),
    (r'^create/$', 'create_experiment'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/add/user/'
     '(?P<username>[\w\.]+)$', 'add_experiment_access_user'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/remove/user/'
     '(?P<username>[\w\.]+)/$', 'remove_experiment_access_user'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/change/user/'
     '(?P<username>[\w\.]+)/$', 'change_user_permissions'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/user/$',
     'retrieve_access_list_user'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/add/group/'
     '(?P<groupname>[\w\s\.]+)$', 'add_experiment_access_group'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/remove/group/'
     '(?P<group_id>\d+)/$', 'remove_experiment_access_group'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/change/group/'
     '(?P<group_id>\d+)/$', 'change_group_permissions'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/group/$',
     'retrieve_access_list_group'),
    (r'^control_panel/(?P<experiment_id>\d+)/access_list/external/$',
     'retrieve_access_list_external'),
    (r'^control_panel/$', 'control_panel'),

    )

accounts_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^login/$', 'login'),
    (r'^manage_auth_methods/$', 'manage_auth_methods'),
    (r'^register/$', register,
     {'form_class': RegistrationForm}),
    (r'', include('registration.urls')),
    )

datafile_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^search/$', 'search_datafile')
)

ajax_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^parameters/(?P<dataset_file_id>\d+)/$', 'retrieve_parameters'),
    (r'^dataset_metadata/(?P<dataset_id>\d+)/$', 'retrieve_dataset_metadata'),
    (r'^datafile_list/(?P<dataset_id>\d+)/$', 'retrieve_datafile_list'),
    (r'^user_list/$', 'retrieve_user_list'),
    (r'^group_list/$', 'retrieve_group_list'),
    (r'^upload_complete/$', 'upload_complete'),
    (r'^upload_files/(?P<dataset_id>\d+)/$', 'upload_files'),
    (r'^experiment_description/(?P<experiment_id>\d+)/$',
     'experiment_description'),
    (r'^experiment_datasets/(?P<experiment_id>\d+)/$', 'experiment_datasets'),
    )

download_urls = patterns(
    'tardis.tardis_portal.download',
    (r'^datafile/(?P<datafile_id>\d+)/$', 'download_datafile'),
    #(r'^dataset/(?P<dataset_id>\d+)/$', 'download_dataset'),
    (r'^experiment/(?P<experiment_id>\d+)/$', 'download_experiment'),
    (r'^datafiles/$', 'download_datafiles'),
    )

group_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^(?P<group_id>\d+)/$', 'retrieve_group_userlist'),
    (r'^(?P<group_id>\d+)/add/(?P<username>[\w\.]+)$',
     'add_user_to_group'),
    (r'^(?P<group_id>\d+)/remove/(?P<username>[\w\.]+)/$',
     'remove_user_from_group'),
    )

display_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^ExperimentImage/load/(?P<parameter_id>\d+)/$',
     'load_experiment_image'),
    (r'^DatasetImage/load/(?P<parameter_id>\d+)/'
     '(?P<parameter_name>\w+)/$',
     'load_dataset_image'),
    (r'^DatafileImage/load/(?P<parameter_id>\d+)/$',
     'load_datafile_image'),
    (r'^ExperimentImage/(?P<experiment_id>\d+)/'
     '(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$',
     'display_experiment_image'),
    (r'^DatasetImage/(?P<dataset_id>\d+)/(?P<parameterset_id>\d+)/'
     '(?P<parameter_name>\w+)/$',
     'display_dataset_image'),
    (r'^DatafileImage/(?P<dataset_file_id>\d+)/'
     '(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$',
     'display_datafile_image'),
    )

urlpatterns = patterns(
    # (r'^search/quick/$', 'tardis.tardis_portal.views.search_quick'),
    '',
    (r'', include(core_urls)),

    # Equipment views
    (r'^equipment/', include('tardis.apps.equipment.urls')),

    # Experiment Views
    (r'^experiment/', include(experiment_urls)),

    # Experiment Views
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

    # Display Views
    (r'^display/', include(display_urls)),

    # Login/out
    (r'^login/$', 'tardis.tardis_portal.views.login'),
    (r'^logout/$', logout, {'next_page': '/'}),

    # Media
    (r'site_media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_DOC_ROOT}),
    (r'media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.ADMIN_MEDIA_STATIC_DOC_ROOT}),

    # Admin
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^upload/(?P<dataset_id>\d+)/$', 'tardis.tardis_portal.views.upload'),
)
