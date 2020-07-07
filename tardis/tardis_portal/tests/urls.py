from django.conf.urls import include, url
from django.contrib.auth.urls import urlpatterns
from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.template import Template, RequestContext

from tardis.apps import sftp

from ...urls.accounts import accounts_urls
from ...urls.download import download_urls
from ...urls.group import group_urls
from .. import download
from ..views.pages import ExperimentView
from ..views import load_datafile_image
from ..views import load_dataset_image
from ..views import load_experiment_image

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

    # Needed for user_menu context processor:
    url(r'^accounts/', include(accounts_urls)),
    url(r'^download/', include(download_urls)),
    url(r'^groups/', include(group_urls)),
    url(r'^apps/sftp/', include(sftp.urls)),
    url(r'^logout/$', LogoutView.as_view(), {'next_page': '/'},
        name='logout'),
]
