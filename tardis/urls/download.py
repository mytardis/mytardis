"""
Download URLs
"""
from django.urls import re_path

from tardis.tardis_portal.download import (
    download_api_key,
    download_datafile,
    streaming_download_datafiles,
    streaming_download_dataset,
    streaming_download_experiment,
)

download_urls = [
    re_path(
        r"^datafile/(?P<datafile_id>\d+)/$",
        download_datafile,
        name="tardis.tardis_portal.download.download_datafile",
    ),
    re_path(
        r"^datafiles/$",
        streaming_download_datafiles,
        name="tardis.tardis_portal.download.streaming_download_datafiles",
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/$",
        streaming_download_experiment,
        name="tardis.tardis_portal.download.streaming_download_experiment",
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/"
        r"(?P<comptype>[a-z]{3})/$",  # tgz or tar
        streaming_download_experiment,
        name="tardis.tardis_portal.download.streaming_download_experiment",
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/"
        r"(?P<comptype>[a-z]{3})/(?P<organization>[^/]+)/$",
        streaming_download_experiment,
    ),
    re_path(
        r"^dataset/(?P<dataset_id>\d+)/$",
        streaming_download_dataset,
        name="tardis.tardis_portal.download.streaming_download_dataset",
    ),
    re_path(
        r"^dataset/(?P<dataset_id>\d+)/" + r"(?P<comptype>[a-z]{3})/$",  # tgz or tar
        streaming_download_dataset,
        name="tardis.tardis_portal.download.streaming_download_dataset",
    ),
    re_path(
        r"^dataset/(?P<dataset_id>\d+)/"
        r"(?P<comptype>[a-z]{3})/(?P<organization>[^/]+)/$",
        streaming_download_dataset,
        name="tardis.tardis_portal.download.streaming_download_dataset",
    ),
    re_path(
        r"^api_key/$",
        download_api_key,
        name="tardis.tardis_portal.download.download_api_key",
    ),
]
