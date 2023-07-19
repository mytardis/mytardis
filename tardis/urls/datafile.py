"""
DataFile URLs
"""
from django.urls import include, re_path

from tardis.tardis_portal.download import view_datafile
from tardis.tardis_portal.iiif import download_image, download_info

iiif_urls = [
    re_path(
        r"^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/"
        r"(?P<rotation>[\d\.]+)/(?P<quality>\w+)$",
        download_image,
        name="tardis.tardis_portal.iiif.download_image",
    ),
    re_path(
        r"^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/"
        r"(?P<rotation>[\d\.]+)/(?P<quality>\w+).(?P<format>\w+)$",
        download_image,
        name="tardis.tardis_portal.iiif.download_image",
    ),
    re_path(
        r"^(?P<datafile_id>\d+)/info.(?P<format>\w+)$",
        download_info,
        name="tardis.tardis_portal.iiif.download_info",
    ),
]

datafile_urls = [
    re_path(
        r"^view/(?P<datafile_id>\d+)/$",
        view_datafile,
        name="tardis.tardis_portal.download.view_datafile",
    ),
    re_path(r"^iiif/", include(iiif_urls)),
]
