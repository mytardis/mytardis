'''
Download URLs
'''
from django.conf.urls import url

from tardis.tardis_portal.download import (
    download_datafile,
    streaming_download_datafiles,
    streaming_download_experiment,
    streaming_download_dataset,
    download_api_key
)

download_urls = [
    url(r'^datafile/(?P<datafile_id>\d+)/$', download_datafile,
        name='tardis.tardis_portal.download.download_datafile'),
    url(r'^datafiles/$', streaming_download_datafiles,
        name='tardis.tardis_portal.download.streaming_download_datafiles'),
    url(r'^experiment/(?P<experiment_id>\d+)/$',
        streaming_download_experiment,
        name='tardis.tardis_portal.download.streaming_download_experiment'),
    url(r'^experiment/(?P<experiment_id>\d+)/'
        r'(?P<comptype>[a-z]{3})/$',  # tgz or tar
        streaming_download_experiment,
        name='tardis.tardis_portal.download.streaming_download_experiment'),
    url(r'^experiment/(?P<experiment_id>\d+)/'
        r'(?P<comptype>[a-z]{3})/(?P<organization>[^/]+)/$',
     streaming_download_experiment),
    url(r'^dataset/(?P<dataset_id>\d+)/$',
        streaming_download_dataset,
        name='tardis.tardis_portal.download.streaming_download_dataset'),
    url(r'^dataset/(?P<dataset_id>\d+)/'
        r'(?P<comptype>[a-z]{3})/$',  # tgz or tar
        streaming_download_dataset,
        name='tardis.tardis_portal.download.streaming_download_dataset'),
    url(r'^dataset/(?P<dataset_id>\d+)/'
        r'(?P<comptype>[a-z]{3})/(?P<organization>[^/]+)/$',
        streaming_download_dataset,
        name='tardis.tardis_portal.download.streaming_download_dataset'),
    url(r'^api_key/$', download_api_key,
        name='tardis.tardis_portal.download.download_api_key'),
]
