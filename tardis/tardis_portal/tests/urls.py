from django.contrib.auth.urls import urlpatterns
from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.template import RequestContext, Template
from django.urls import include, re_path

from tardis.apps import sftp

from ...urls.accounts import accounts_urls
from ...urls.download import download_urls
from .. import download
from ..views import load_datafile_image, load_dataset_image, load_experiment_image
from ..views.pages import ExperimentView


def groups_view(request):
    """
    Dummy view for remote user tests
    """

    t = Template("Groups are {% for p, g in groups %}({{ p }},{{ g }}) {% endfor %}.")
    c = RequestContext(request, {"groups": request.user.userprofile.ext_groups})
    return HttpResponse(t.render(c))


# special urls for auth test cases
urlpatterns += [
    re_path(r"^test/groups/$", groups_view),
    re_path(
        r"^test/experiment/view/(?P<experiment_id>\d+)/$", ExperimentView.as_view()
    ),
    re_path(
        r"^test/download/datafile/(?P<datafile_id>\d+)/$",
        download.download_datafile,
        name="tardis.tardis_portal.download.download_datafile",
    ),
    re_path(
        r"^test/ExperimentImage/load/(?P<parameter_id>\d+)/$",
        load_experiment_image,
        name="tardis.tardis_portal.views.load_experiment_image",
    ),
    re_path(
        r"^test/DatasetImage/load/(?P<parameter_id>\d+)/$",
        load_dataset_image,
        name="tardis.tardis_portal.views.load_dataset_image",
    ),
    re_path(
        r"^test/DatafileImage/load/(?P<parameter_id>\d+)/$",
        load_datafile_image,
        name="tardis.tardis_portal.views.load_datafile_image",
    ),
    re_path(
        r"^test/experiment/view/(?P<experiment_id>\d+)/$", ExperimentView.as_view()
    ),
    # Needed for user_menu context processor:
    re_path(r"^accounts/", include(accounts_urls)),
    re_path(r"^download/", include(download_urls)),
    re_path(r"^apps/sftp/", include(sftp.urls)),
    re_path(r"^logout/$", LogoutView.as_view(), {"next_page": "/"}, name="logout"),
]
