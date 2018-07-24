'''
Dataset URLs
'''
from django.conf.urls import url

from tardis.tardis_portal.views import DatasetView
from tardis.tardis_portal.views import (
    edit_dataset,
    dataset_thumbnail,
    checksums_download
)

dataset_urls = [
    url(r'^(?P<dataset_id>\d+)$', DatasetView.as_view(),
        name='tardis_portal.view_dataset'),
    url(r'^(?P<dataset_id>\d+)/edit$', edit_dataset,
        name='tardis.tardis_portal.views.edit_dataset'),
    url(r'^(?P<dataset_id>\d+)/thumbnail$', dataset_thumbnail,
        name='tardis.tardis_portal.views.dataset_thumbnail'),
    url(r'^(?P<dataset_id>\d+)/checksums$', checksums_download,
        name='tardis_portal.dataset_checksums'),
]
