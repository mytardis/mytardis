from django.conf import settings
from django.conf.urls import url

from .ajax_pages import (
    project_latest_experiment,
    project_recent_experiments,
    retrieve_project_metadata,
)
from .views import (
    ProjectView,
    create_project,
    edit_project,
    my_projects,
    public_projects,
    retrieve_owned_proj_list,
    add_project_par,
    edit_project_par,
)


# TODO point these to alterntive pages when they are developed

project_urls = [
    url(
        r"^view/(?P<project_id>\d+)/$",
        ProjectView.as_view(),
        name="tardis.apps.projects.view_project",
    ),
    url(
        r"^edit/(?P<project_id>\d+)/$",
        edit_project,
        name="tardis.apps.projects.edit_project",
    ),
    url(r"^myprojects/$", my_projects, name="tardis.apps.projects.views.my_projects"),
    url(
        r"^public_projects/$",
        public_projects,
        name="tardis.apps.projects.views.public_projects",
    ),
    url(
        r"^ajax/owned_proj_list/$",
        retrieve_owned_proj_list,
        name="tardis.apps.projects.retrieve_owned_proj_list",
    ),
    url(
        r"^ajax/(?P<project_id>\d+)/latest_experiment$",
        project_latest_experiment,
        name="tardis.apps.projects.project_latest_experiment",
    ),
    url(
        r"^ajax/(?P<project_id>\d+)/recent_experiments$",
        project_recent_experiments,
        name="tardis.apps.projects.project_recent_experiments",
    ),
    url(
        r"^project_metadata/(?P<project_id>\d+)/$",
        retrieve_project_metadata,
        name="tardis.apps.projects.retrieve_project_metadata",
    ),
    url(
        r"^add_project_parameters/(?P<project_id>\d+)/$",
        add_project_par,
        name="tardis.apps.projects.views.add_project_par",
    ),
    url(
        r"^edit_project_parameters/(?P<parameterset_id>\d+)/$",
        edit_project_par,
        name="tardis.apps.projects.views.edit_project_par",
    ),
]


if not settings.DISABLE_CREATION_FORMS:
    project_urls += [
        url(r"^create/$", create_project, name="tardis.apps.projects.create_project"),
    ]
