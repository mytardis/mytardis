from django.contrib import admin
admin.autodiscover()

from django.contrib.auth.views import logout
from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from registration.views import register

from tardis.tardis_portal.forms import RegistrationForm

from django.http import HttpResponseRedirect, HttpResponse

import django_jasmine.urls

def getTardisApps():
    return map(lambda app: app.split('.').pop(),
               filter(lambda app: app.startswith(settings.TARDIS_APP_ROOT),
                      settings.INSTALLED_APPS))

handler500 = 'tardis.views.error_handler'

core_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^$', 'index'),
    url(r'^site-settings.xml/$', 'site_settings', name='tardis-site-settings'),
    (r'^about/$', 'about'),
    (r'^stats/$', 'stats'),
    (r'^import_params/$', 'import_params'),
    (r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /download/\nDisallow: /stats/", mimetype="text/plain"))
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
    (r'^view/$', 'experiment_index'), # Legacy URL
    (r'^search/$', 'search_experiment'),
    (r'^register/$', 'register_experiment_ws_xmldata'),
    (r'^metsexport/(?P<experiment_id>\d+)/$', 'metsexport_experiment'),
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
    (r'^view/(?P<experiment_id>\d+)/public_access_badge/$', 'experiment_public_access_badge'),
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
    (r'^register/$', register,
     {'form_class': RegistrationForm,
      'backend': 'registration.backends.default.DefaultBackend'}),
    (r'', include('registration.urls')),
    )

dataset_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^(?P<dataset_id>\d+)/stage-files$', 'stage_files_to_dataset'),
    (r'^(?P<dataset_id>\d+)$', 'view_dataset'),
    (r'^(?P<dataset_id>\d+)/edit$', 'edit_dataset'),
)
iiif_urls = patterns(
    'tardis.tardis_portal.iiif',
    url(r'^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/(?P<rotation>[\d\.]+)/(?P<quality>\w+)$', 'download_image'),
    url(r'^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/(?P<rotation>[\d\.]+)/(?P<quality>\w+).(?P<format>\w+)$', 'download_image'),
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
    (r'^experiment/(?P<experiment_id>\d+)/dataset/$', 'experiment_datasets_json'),
    (r'^experiment/(?P<experiment_id>\d+)/dataset/(?P<dataset_id>\d+)$', 'dataset_json'),
)

ajax_urls = patterns(
    'tardis.tardis_portal.views',
    (r'^parameters/(?P<dataset_file_id>\d+)/$', 'retrieve_parameters'),
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
    (r'^experiment/(?P<experiment_id>\d+)/dataset-transfer$', 'experiment_dataset_transfer'),
    (r'^license/list$', 'retrieve_licenses'),
    (r'^json/', include(json_urls))
)

download_urls = patterns(
    'tardis.tardis_portal.download',
    (r'^datafile/(?P<datafile_id>\d+)/$', 'download_datafile'),
    (r'^experiment/(?P<experiment_id>\d+)/(?P<comptype>[a-z]{3})/$',
     'download_experiment'),
    (r'^datafiles/$', 'download_datafiles'),
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
    (r'^DatafileImage/(?P<dataset_file_id>\d+)/'
     '(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$',
     'display_datafile_image'),
    )

apppatterns = patterns('',)
for app in getTardisApps():
    apppatterns += patterns('tardis.apps',
                            (r'^%s/' % app.replace('_','-'),
                             include('%s.%s.urls' %
                                     (settings.TARDIS_APP_ROOT, app))))
urlpatterns = patterns(
    # (r'^search/quick/$', 'tardis.tardis_portal.views.search_quick'),
    '',
    (r'', include(core_urls)),
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

    # Display Views
    (r'^display/', include(display_urls)),

    # Login/out
    (r'^login/$', 'tardis.tardis_portal.views.login'),
    (r'^logout/$', logout, {'next_page': '/'}),

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
                                                                          