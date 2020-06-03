from django.conf.urls import url

from tardis.tardis_portal.views import (
    ProjectView,
    ReactProject
    )

from tardis.tardis_portal.views import (
    create_project,
    edit_project
    )


#TODO point these to alterntive pages when they are developed

project_urls = [
    # warrick test
    # maps to /project/react/
    url(r'^react/$', ReactProject.as_view(),
        name='tardis_portal.views.react_project'),
    # url(r'^react/(?P<project_id>\d+)/$', react_project,
    #     name='tardis_portal.views.react_project'),

    url(r'^(?P<project_id>\d+)/$', ProjectView.as_view(),
        name='tardis_portal.views.create_project'),
    url(r'^edit/?P<project_id>\d+/$', edit_project,
        name='tardis.tardis_portal.views.edit_project'),
    url(r'^create/$', create_project,
        name='tardis.tardis_portal.views.create_project')
    ]
