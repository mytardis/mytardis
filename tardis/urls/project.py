from django.conf.urls import url

from tardis.tardis_portal.views import ProjectView
from tardis.tardis_portal.views import (
    create_project,
    edit_project
    )

project_urls = [
    url(r'^(?P<project_id>\d+)$', ProjectView.as_view(),
        name='tardis_portal.view_project'),
    url(r'^edit/?P<project_id>\d+/$', edit_project,
        name='tardis.tardis_portal.views.edit_project'),
    url(r'^create/$', create_project,
        name='tardis.tardis_portal.views.create_project')
    ]
