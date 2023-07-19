"""
Core URLs
"""
from django.http import HttpResponse
from django.urls import re_path

from tardis.tardis_portal.views import (
    about,
    healthz,
    my_data,
    public_data,
    shared,
    site_settings,
    stats,
)

core_urls = [
    re_path(r"^healthz$", healthz, name="tardis.tardis_portal.views.healthz"),
    re_path(r"^site-settings.xml/$", site_settings, name="tardis-site-settings"),
    re_path(r"^mydata/$", my_data, name="tardis.tardis_portal.views.my_data"),
    re_path(r"^shared/$", shared, name="tardis.tardis_portal.views.shared"),
    re_path(
        r"^public_data/", public_data, name="tardis.tardis_portal.views.public_data"
    ),
    re_path(r"^about/$", about, name="tardis.tardis_portal.views.about"),
    re_path(r"^stats/$", stats, name="tardis.tardis_portal.views.stats"),
    re_path(
        r"^robots\.txt$",
        lambda r: HttpResponse(
            "User-agent: *\nDisallow: /download/\nDisallow: /stats/",
            content_type="text/plain",
        ),
    ),
]
