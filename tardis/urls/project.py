from django.conf.urls import url

from tardis.tardis_portal.views import (
    ProjectView,
    #ProjectDetails
    )

from tardis.tardis_portal.views import (
    create_project,
    edit_project
    )


#TODO point these to alterntive pages when they are developed

project_urls = [
    #url(r'^view/(?P<project_id>\d+)$', ProjectDetails.as_view(),
    #    name='tardis_portal.views.react_project'),

    url(r'^view/(?P<project_id>\d+)$', ProjectView.as_view(),
        name='tardis_portal.view_project'),
    url(r'^edit/?P<project_id>\d+/$', edit_project,
        name='tardis.tardis_portal.views.edit_project'),
    url(r'^create/$', create_project,
        name='tardis.tardis_portal.views.create_project')
    ]
