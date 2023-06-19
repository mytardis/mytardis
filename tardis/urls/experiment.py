"""
URLs for experiments
"""
from django.conf import settings
from django.urls import re_path

from tardis.tardis_portal.views import (
    ExperimentView,
    add_dataset,
    add_experiment_access_group,
    add_experiment_access_user,
    create_experiment,
    create_group,
    create_token,
    create_user,
    edit_experiment,
    remove_experiment_access_group,
    remove_experiment_access_user,
    retrieve_access_list_external,
    retrieve_access_list_group,
    retrieve_access_list_group_readonly,
    retrieve_access_list_tokens,
    retrieve_access_list_user,
    retrieve_access_list_user_readonly,
    view_rifcs,
)

user_pattern = "[\w\-][\w\-\.]+(@[\w\-][\w\-\.]+[a-zA-Z]{1,4})*"

experiment_urls = [
    re_path(
        r"^view/(?P<experiment_id>\d+)/$",
        ExperimentView.as_view(),
        name="tardis_portal.view_experiment",
    ),
    re_path(
        r"^edit/(?P<experiment_id>\d+)/$",
        edit_experiment,
        name="tardis.tardis_portal.views.edit_experiment",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/add/user/"
        "(?P<username>%s)/$" % user_pattern,
        add_experiment_access_user,
        name="tardis.tardis_portal.views.add_experiment_access_user",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/remove/user/"
        "(?P<username>%s)/$" % user_pattern,
        remove_experiment_access_user,
        name="tardis.tardis_portal.views.remove_experiment_access_user",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/user/$",
        retrieve_access_list_user,
        name="tardis.tardis_portal.views.retrieve_access_list_user",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/user/readonly/$",
        retrieve_access_list_user_readonly,
        name="tardis.tardis_portal.views.retrieve_access_list_user_readonly",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/add/group/"
        "(?P<groupname>.+)/$",
        add_experiment_access_group,
        name="tardis.tardis_portal.views.add_experiment_access_group",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/remove/group/"
        "(?P<group_id>\d+)/$",
        remove_experiment_access_group,
        name="tardis.tardis_portal.views.remove_experiment_access_group",
    ),
    re_path(
        r"^control_panel/create/group/$",
        create_group,
        name="tardis.tardis_portal.views.create_group",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/group/$",
        retrieve_access_list_group,
        name="tardis.tardis_portal.views.retrieve_access_list_group",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/group/readonly/$",
        retrieve_access_list_group_readonly,
        name="tardis.tardis_portal.views.retrieve_access_list_group_readonly",
    ),
    re_path(
        r"^control_panel/create/user/$",
        create_user,
        name="tardis.tardis_portal.views.create_user",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/external/$",
        retrieve_access_list_external,
        name="tardis.tardis_portal.views.retrieve_access_list_external",
    ),
    re_path(
        r"^control_panel/(?P<experiment_id>\d+)/access_list/tokens/$",
        retrieve_access_list_tokens,
        name="tardis.tardis_portal.views.retrieve_access_list_tokens",
    ),
    re_path(
        r"^view/(?P<experiment_id>\d+)/create_token/$",
        create_token,
        name="tardis.tardis_portal.views.create_token",
    ),
    re_path(
        r"^view/(?P<experiment_id>\d+)/rifcs/$",
        view_rifcs,
        name="tardis.tardis_portal.views.control_panel.view_rifcs",
    ),
]

if not settings.DISABLE_CREATION_FORMS:
    experiment_urls += [
        re_path(
            r"^create/$",
            create_experiment,
            name="tardis.tardis_portal.views.create_experiment",
        ),
        re_path(
            r"^(?P<experiment_id>\d+)/add-dataset$",
            add_dataset,
            name="tardis.tardis_portal.views.add_dataset",
        ),
    ]
