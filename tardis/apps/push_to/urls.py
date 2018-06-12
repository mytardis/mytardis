from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^signing-services/$', views.get_signing_services),
    url(r'^accessible-hosts/$', views.get_accessible_hosts),
    url(r'^signing-services/(?P<obj_type>[a-z]+)/(?P<push_obj_id>\d+)/$',
        views.get_signing_services),
    url(r'^accessible-hosts/(?P<obj_type>[a-z]+)/(?P<push_obj_id>\d+)/$',
        views.get_accessible_hosts),
    url(r'^accessible-hosts/$', views.get_accessible_hosts),
    url(r'^push/host/(?P<remote_host_id>\d+)/experiment/(?P<experiment_id>\d+)/$',
        views.initiate_push_experiment),
    url(r'^push/host/(?P<remote_host_id>\d+)/dataset/(?P<dataset_id>\d+)/$',
        views.initiate_push_dataset),
    url(r'^push/host/(?P<remote_host_id>\d+)/datafile/(?P<datafile_id>\d+)/$',
        views.initiate_push_datafile),
    url(r'^push/experiment/(?P<experiment_id>\d+)/$',
        views.initiate_push_experiment,
        name='tardis.apps.push_to.views.initiate_push_experiment'),
    url(r'^push/dataset/(?P<dataset_id>\d+)/$', views.initiate_push_dataset,
        name='tardis.apps.push_to.views.initiate_push_dataset'),
    url(r'^push/datafile/(?P<datafile_id>\d+)/$',
        views.initiate_push_datafile),
    url(r'^ssh-authz/host/(?P<remote_host_id>\d+)/$',
        views.authorize_remote_access),
    url(r'^ssh-authz/sign/(?P<service_id>\d+)/host/(?P<remote_host_id>\d+)/$',
        views.authorize_remote_access),
    url(r'^ssh-authz/oauth/callback/$', views.oauth_callback),
    url(r'^ajax/validate-path/(?P<remote_host_id>\d+)/', views.validate_remote_path)
]
