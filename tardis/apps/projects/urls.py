from django.conf.urls import url

from .views import (
    ProjectView,
    create_project,
    edit_project,
    my_projects,
    retrieve_owned_proj_list,
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
    url(r"^create/$", create_project, name="tardis.apps.projects.create_project"),
    url(r"^myprojects/$", my_projects, name="tardis.apps.projects.views.my_projects"),
    url(
        r"^owned_proj_list/$",
        retrieve_owned_proj_list,
        name="tardis.apps.projects.retrieve_owned_proj_list",
    ),
]
