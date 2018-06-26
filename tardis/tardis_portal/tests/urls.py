from django.conf.urls import url
from django.contrib.auth.urls import urlpatterns
from django.http import HttpResponse
from django.template import Template, RequestContext

from tardis.tardis_portal import download
from tardis.tardis_portal.views.pages import ExperimentView
from tardis.tardis_portal.views import load_datafile_image
from tardis.tardis_portal.views import load_dataset_image
from tardis.tardis_portal.views import load_experiment_image
from . import mock_vbl_download

def groups_view(request):
    """
    Dummy view for remote user tests
    """

    t = Template(
            "Groups are {% for p, g in groups %}({{ p }},{{ g }}) {% endfor %}.")
    c = RequestContext(request,
                       {'groups': request.user.userprofile.ext_groups})
    return HttpResponse(t.render(c))


# special urls for auth test cases
urlpatterns += [
    url(r'^test/groups/$', groups_view),
    url(r'^test/experiment/view/(?P<experiment_id>\d+)/$',
        ExperimentView.as_view()),
    url(r'^test/download/datafile/(?P<datafile_id>\d+)/$',
        download.download_datafile,
        name='tardis.tardis_portal.download.download_datafile'),
    url(r'^test/vbl/download/datafile/(?P<datafile_id>\d+)/$',
        mock_vbl_download.download_datafile,
        name='tardis.tardis_portal.tests.'
        'mock_vbl_download.download_datafile'),
    url(r'^test/ExperimentImage/load/(?P<parameter_id>\d+)/$',
        load_experiment_image,
        name='tardis.tardis_portal.views.load_experiment_image'),
    url(r'^test/DatasetImage/load/(?P<parameter_id>\d+)/$',
        load_dataset_image,
        name='tardis.tardis_portal.views.load_dataset_image'),
    url(r'^test/DatafileImage/load/(?P<parameter_id>\d+)/$',
        load_datafile_image,
        name='tardis.tardis_portal.views.load_datafile_image'),
    url(r'^test/experiment/view/(?P<experiment_id>\d+)/$',
        ExperimentView.as_view()),
]
