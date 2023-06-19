"""
AJAX URLS
"""
from django.urls import include, re_path

from tardis.tardis_portal.views import (
    add_datafile_par,
    add_dataset_par,
    add_experiment_par,
    cache_dataset,
    choose_rights,
    dataset_json,
    display_datafile_details,
    edit_datafile_par,
    edit_dataset_par,
    edit_experiment_par,
    experiment_dataset_transfer,
    experiment_datasets,
    experiment_datasets_json,
    experiment_description,
    experiment_latest_dataset,
    experiment_recent_datasets,
    feedback,
    get_experiment_list,
    get_experiment_permissions,
    retrieve_datafile_list,
    retrieve_dataset_metadata,
    retrieve_experiment_metadata,
    retrieve_group_list,
    retrieve_group_list_by_user,
    retrieve_licenses,
    retrieve_owned_exps_list,
    retrieve_parameters,
    retrieve_shared_exps_list,
    retrieve_user_list,
    share,
    upload_complete,
)

json_urls = [
    re_path(
        r"^dataset/(?P<dataset_id>\d+)$",
        dataset_json,
        name="tardis.tardis_portal.views.dataset_json",
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/dataset/$",
        experiment_datasets_json,
        name="tardis.tardis_portal.views.experiment_datasets_json",
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/dataset/(?P<dataset_id>\d+)$",
        dataset_json,
        name="tardis.tardis_portal.views.dataset_json",
    ),
    re_path(
        r"^experiment_list/$",
        get_experiment_list,
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/get_experiment_permissions$",
        get_experiment_permissions,
        name="tardis.tardis_portal.views.get_experiment_permissions",
    ),
]

ajax_urls = [
    re_path(r"^parameters/(?P<datafile_id>\d+)/$", retrieve_parameters),
    re_path(r"^datafile_details/(?P<datafile_id>\d+)/$", display_datafile_details),
    re_path(
        r"^dataset_metadata/(?P<dataset_id>\d+)/$",
        retrieve_dataset_metadata,
        name="tardis.tardis_portal.views.retrieve_dataset_metadata",
    ),
    re_path(
        r"^experiment_metadata/(?P<experiment_id>\d+)/$",
        retrieve_experiment_metadata,
        name="tardis.tardis_portal.views.retrieve_experiment_metadata",
    ),
    re_path(
        r"^datafile_list/(?P<dataset_id>\d+)/$",
        retrieve_datafile_list,
        name="tardis.tardis_portal.views.retrieve_datafile_list",
    ),
    re_path(
        r"^cache_dataset/(?P<dataset_id>\d+)/$", cache_dataset, name="cache_dataset"
    ),
    re_path(r"^user_list/$", retrieve_user_list),
    re_path(r"^group_list/$", retrieve_group_list),
    re_path(r"^group_list_by_user/$", retrieve_group_list_by_user),
    re_path(r"^upload_complete/$", upload_complete),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/description$",
        experiment_description,
        name="tardis.tardis_portal.views.experiment_description",
    ),
    re_path(r"^experiment/(?P<experiment_id>\d+)/datasets$", experiment_datasets),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/latest_dataset$", experiment_latest_dataset
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/recent_datasets$",
        experiment_recent_datasets,
    ),
    re_path(
        r"^owned_exps_list/$",
        retrieve_owned_exps_list,
        name="tardis.tardis_portal.views.retrieve_owned_exps_list",
    ),
    re_path(
        r"^shared_exps_list/$",
        retrieve_shared_exps_list,
        name="tardis.tardis_portal.views.retrieve_shared_exps_list",
    ),
    re_path(
        r"^edit_datafile_parameters/(?P<parameterset_id>\d+)/$",
        edit_datafile_par,
        name="tardis.tardis_portal.views.edit_datafile_par",
    ),
    re_path(
        r"^edit_dataset_parameters/(?P<parameterset_id>\d+)/$",
        edit_dataset_par,
        name="tardis.tardis_portal.views.edit_dataset_par",
    ),
    re_path(
        r"^edit_experiment_parameters/(?P<parameterset_id>\d+)/$",
        edit_experiment_par,
        name="tardis.tardis_portal.views.edit_experiment_par",
    ),
    re_path(
        r"^add_datafile_parameters/(?P<datafile_id>\d+)/$",
        add_datafile_par,
        name="tardis.tardis_portal.views.add_datafile_par",
    ),
    re_path(
        r"^add_dataset_parameters/(?P<dataset_id>\d+)/$",
        add_dataset_par,
        name="tardis.tardis_portal.views.add_dataset_par",
    ),
    re_path(
        r"^add_experiment_parameters/(?P<experiment_id>\d+)/$",
        add_experiment_par,
        name="tardis.tardis_portal.views.add_experiment_par",
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/rights$",
        choose_rights,
        name="tardis.tardis_portal.views.choose_rights",
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/share$",
        share,
        name="tardis.tardis_portal.views.share",
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/dataset-transfer$",
        experiment_dataset_transfer,
        name="tardis.tardis_portal.views.experiment_dataset_transfer",
    ),
    re_path(
        r"^license/list$",
        retrieve_licenses,
        name="tardis.tardis_portal.views.retrieve_licenses",
    ),
    re_path(r"^json/", include(json_urls)),
    re_path(r"^feedback/", feedback, name="tardis.tardis_portal.views.feedback"),
]
