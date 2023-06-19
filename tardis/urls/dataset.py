"""
Dataset URLs
"""
from django.urls import re_path

from tardis.tardis_portal.views import (
    DatasetView,
    checksums_download,
    dataset_thumbnail,
    edit_dataset,
)

dataset_urls = [
    re_path(
        r"^(?P<dataset_id>\d+)$",
        DatasetView.as_view(),
        name="tardis_portal.view_dataset",
    ),
    re_path(
        r"^(?P<dataset_id>\d+)/edit$",
        edit_dataset,
        name="tardis.tardis_portal.views.edit_dataset",
    ),
    re_path(
        r"^(?P<dataset_id>\d+)/thumbnail$",
        dataset_thumbnail,
        name="tardis.tardis_portal.views.dataset_thumbnail",
    ),
    re_path(
        r"^(?P<dataset_id>\d+)/checksums$",
        checksums_download,
        name="tardis_portal.dataset_checksums",
    ),
]
