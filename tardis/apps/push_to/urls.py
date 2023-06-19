from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^signing-services/$", views.get_signing_services),
    re_path(r"^accessible-hosts/$", views.get_accessible_hosts),
    re_path(
        r"^signing-services/(?P<obj_type>[a-z]+)/(?P<push_obj_id>\d+)/$",
        views.get_signing_services,
    ),
    re_path(
        r"^accessible-hosts/(?P<obj_type>[a-z]+)/(?P<push_obj_id>\d+)/$",
        views.get_accessible_hosts,
    ),
    re_path(r"^accessible-hosts/$", views.get_accessible_hosts),
    re_path(
        r"^push/host/(?P<remote_host_id>\d+)/experiment/(?P<experiment_id>\d+)/$",
        views.initiate_push_experiment,
        name="tardis.apps.push_to.views.initiate_push_experiment",
    ),
    re_path(
        r"^push/host/(?P<remote_host_id>\d+)/dataset/(?P<dataset_id>\d+)/$",
        views.initiate_push_dataset,
        name="tardis.apps.push_to.views.initiate_push_dataset",
    ),
    re_path(
        r"^push/host/(?P<remote_host_id>\d+)/datafile/(?P<datafile_id>\d+)/$",
        views.initiate_push_datafile,
    ),
    re_path(
        r"^push/experiment/(?P<experiment_id>\d+)/$",
        views.initiate_push_experiment,
        name="tardis.apps.push_to.views.initiate_push_experiment",
    ),
    re_path(
        r"^push/dataset/(?P<dataset_id>\d+)/$",
        views.initiate_push_dataset,
        name="tardis.apps.push_to.views.initiate_push_dataset",
    ),
    re_path(r"^push/datafile/(?P<datafile_id>\d+)/$", views.initiate_push_datafile),
    re_path(
        r"^ssh-authz/host/(?P<remote_host_id>\d+)/$", views.authorize_remote_access
    ),
    re_path(
        r"^ssh-authz/sign/(?P<service_id>\d+)/host/(?P<remote_host_id>\d+)/$",
        views.authorize_remote_access,
    ),
    re_path(r"^ssh-authz/oauth/callback/$", views.oauth_callback),
    re_path(
        r"^ajax/validate-path/(?P<remote_host_id>\d+)/", views.validate_remote_path
    ),
]
