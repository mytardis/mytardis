import logging
from os import path

from django.contrib import admin

from django.contrib.auth.views import LogoutView
from django.conf.urls import include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve

from tardis.app_config import get_tardis_apps
from tardis.app_config import format_app_name_for_url
from tardis.tardis_portal.views import IndexView

from tardis.tardis_portal.views.pages import site_routed_view
from tardis.tardis_portal.views import upload
from tardis.tardis_portal.views import rcauth
from tardis.tardis_portal.views import login

from .accounts import accounts_urls
from .ajax import ajax_urls
from .api import api_urls
from .api import tastypie_swagger_urls
from .core import core_urls
from .datafile import datafile_urls
from .dataset import dataset_urls
from .display import display_urls
from .download import download_urls
from .experiment import experiment_urls
from .facility import facility_urls
from .group import group_urls
from .token import token_urls

admin.autodiscover()

logger = logging.getLogger(__name__)

handler500 = "tardis.views.error_handler"

rapidconnect_urls = [
    url(r"^auth/jwt$", rcauth),
]

overridable_urls = [
    url(
        r"^$",
        site_routed_view,
        {
            "default_view": IndexView.as_view(),
            "site_mappings": getattr(settings, "INDEX_VIEWS", {}),
        },
        name="tardis.tardis_portal.views.index",
    ),
    url(
        r"^login/$",
        site_routed_view,
        {"default_view": login, "site_mappings": getattr(settings, "LOGIN_VIEWS", {})},
        name="tardis.tardis_portal.views.login",
    ),
]

app_urls = []
for app_name, app in get_tardis_apps():
    try:
        if app_name == "projects":
            continue
        app_urls += [
            url(r"^%s/" % format_app_name_for_url(app_name), include("%s.urls" % app))
        ]
    except:
        pass

urlpatterns = [
    url(r"", include(core_urls)),
    # API views
    url(r"^api/", include(api_urls)),
    # tastypie_swagger endpoints for API auto-documentation
    url(r"^api/", include(tastypie_swagger_urls)),
    # Experiment Views
    url(r"^experiment/", include(experiment_urls)),
    # Dataset Views
    url(r"^dataset/", include(dataset_urls)),
    # Datafile Views
    url(r"^datafile/", include(datafile_urls)),
    # Download Views
    url(r"^download/", include(download_urls)),
    # Ajax Views
    url(r"^ajax/", include(ajax_urls)),
    # Account Views
    url(r"^accounts/", include(accounts_urls)),
    # Group Views
    url(r"^group/", include(group_urls)),
    # Facility views
    url(r"^facility/", include(facility_urls)),
    # Display Views
    url(r"^display/", include(display_urls)),
    # Login/out
    url(r"^logout/$", LogoutView.as_view(), name="logout"),
    # Rapid Connect
    url(r"^rc/", include(rapidconnect_urls)),
    # Admin
    url(r"^admin/doc/", include("django.contrib.admindocs.urls")),
    url(r"^admin/", admin.site.urls),
    # Apps
    url(r"^apps/", include(app_urls)),
    # Token login
    url(r"^token/", include(token_urls)),
    # Class-based views that may be overriden by apps
    url(r"", include(overridable_urls)),
]

if not settings.DISABLE_CREATION_FORMS:
    urlpatterns += [
        url(
            r"^upload/(?P<dataset_id>\d+)/$",
            upload,
            name="tardis.tardis_portal.views.upload",
        ),
    ]


# Import project app urls here to avoid /apps prefix in url
if "tardis.apps.projects" in settings.INSTALLED_APPS:
    from tardis.apps.projects.urls import project_urls

    urlpatterns += (url(r"^project/", include(project_urls)),)


# Handle static files from /static
urlpatterns += staticfiles_urlpatterns()

# Show compiled documentation to developers. Production instances can be
# enabled to show on readthedocs.org
if settings.DEBUG:
    urlpatterns += [
        url(
            r"^docs/(?P<path>.*)$",
            serve,
            {
                "document_root": path.abspath(
                    path.join(path.dirname(__file__), "..", "docs/html/")
                ),
            },
        ),
    ]
