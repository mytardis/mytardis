import logging
from os import path

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, re_path
from django.views.static import serve

from tardis.app_config import get_tardis_apps
from tardis.app_config import format_app_name_for_url
from tardis.apps.search.urls import urlpatterns as search_urls
from tardis.tardis_portal.views import IndexView, rcauth, login, upload
from tardis.tardis_portal.views.pages import site_routed_view

from .accounts import accounts_urls
from .ajax import ajax_urls
from .api import api_urls  # , tastypie_swagger_urls
from .core import core_urls
from .datafile import datafile_urls
from .dataset import dataset_urls
from .display import display_urls
from .download import download_urls
from .experiment import experiment_urls
from .facility import facility_urls
from .group import group_urls
from .token import token_urls
from tardis.apps.yaml_dump.urls import urlpatterns as yamldump_urls

admin.autodiscover()

logger = logging.getLogger(__name__)

handler500 = "tardis.views.error_handler"

rapidconnect_urls = [
    re_path(r"^auth/jwt$", rcauth),
]

overridable_urls = [
    re_path(
        r"^$",
        site_routed_view,
        {
            "default_view": IndexView.as_view(),
            "site_mappings": getattr(settings, "INDEX_VIEWS", {}),
        },
        name="tardis.tardis_portal.views.index",
    ),
    re_path(
        r"^login/$",
        site_routed_view,
        {"default_view": login, "site_mappings": getattr(settings, "LOGIN_VIEWS", {})},
        name="tardis.tardis_portal.views.login",
    ),
]

app_urls = []
for app_name, app in get_tardis_apps():
    try:
        if app_name in ["projects", "search", "yamldump"]:
            continue
        app_urls += [
            re_path(
                r"^%s/" % format_app_name_for_url(app_name), include("%s.urls" % app)
            )
        ]
    except:
        pass

urlpatterns = [
    re_path(r"", include(core_urls)),
    # API views
    re_path(r"^api/", include(api_urls)),
    # tastypie_swagger endpoints for API auto-documentation
    # re_path(r"^api/", include(tastypie_swagger_urls)),
    re_path(r'^yaml/', include(yamldump_urls)),
    # Experiment Views
    re_path(r"^experiment/", include(experiment_urls)),
    # Dataset Views
    re_path(r"^dataset/", include(dataset_urls)),
    # Datafile Views
    re_path(r"^datafile/", include(datafile_urls)),
    # Download Views
    re_path(r"^download/", include(download_urls)),
    # Ajax Views
    re_path(r"^ajax/", include(ajax_urls)),
    # Account Views
    re_path(r"^accounts/", include(accounts_urls)),
    # Group Views
    re_path(r"^group/", include(group_urls)),
    # Facility views
    re_path(r"^facility/", include(facility_urls)),
    # Display Views
    re_path(r"^display/", include(display_urls)),
    # Login/out
    re_path(r"^logout/$", LogoutView.as_view(), name="logout"),
    # Rapid Connect
    re_path(r"^rc/", include(rapidconnect_urls)),
    # Admin
    re_path(r"^admin/doc/", include("django.contrib.admindocs.urls")),
    re_path(r"^admin/", admin.site.urls),
    # Apps
    re_path(r"^apps/", include(app_urls)),
    # Token login
    re_path(r"^token/", include(token_urls)),
    # Class-based views that may be overriden by apps
    re_path(r"", include(overridable_urls)),
    # Explicitly add search, to avoid including /apps/ in url
    re_path(r"^search/", include(search_urls)),
]

if not settings.DISABLE_CREATION_FORMS:
    urlpatterns += [
        re_path(
            r"^upload/(?P<dataset_id>\d+)/$",
            upload,
            name="tardis.tardis_portal.views.upload",
        ),
    ]


# Import project app urls here to avoid /apps prefix in url
if "tardis.apps.projects" in settings.INSTALLED_APPS:
    from tardis.apps.projects.urls import project_urls

    urlpatterns += (re_path(r"^project/", include(project_urls)),)


# Handle static files from /static
urlpatterns += staticfiles_urlpatterns()

# Show compiled documentation to developers. Production instances can be
# enabled to show on readthedocs.org
if settings.DEBUG:
    urlpatterns += [
        re_path(
            r"^docs/(?P<path>.*)$",
            serve,
            {
                "document_root": path.abspath(
                    path.join(path.dirname(__file__), "..", "docs/html/")
                ),
            },
        ),
    ]
