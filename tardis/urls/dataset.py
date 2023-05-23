"""
Dataset URLs
"""
from django.conf.urls import url

from tardis.tardis_portal.views import DatasetView
from tardis.tardis_portal.views import (
    edit_dataset,
    dataset_thumbnail,
    checksums_download,
)

dataset_urls = [
    url(
        r"^view/(?P<dataset_id>\d+)/$",
        DatasetView.as_view(),
        name="tardis_portal.view_dataset",
    ),
    url(
        r"^edit/(?P<dataset_id>\d+)/$",
        edit_dataset,
        name="tardis.tardis_portal.views.edit_dataset",
    ),
    url(
        r"^thumbnail/(?P<dataset_id>\d+)/$",
        dataset_thumbnail,
        name="tardis.tardis_portal.views.dataset_thumbnail",
    ),
    url(
        r"^checksums/(?P<dataset_id>\d+)/$",
        checksums_download,
        name="tardis_portal.dataset_checksums",
    ),
]
