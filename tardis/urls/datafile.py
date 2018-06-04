'''
DataFile URLs
'''
from django.conf.urls import include, url

from tardis.tardis_portal.iiif import (
    download_image,
    download_info
)
from tardis.tardis_portal.download import view_datafile

iiif_urls = [
    url(r'^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/'
        r'(?P<rotation>[\d\.]+)/(?P<quality>\w+)$',
        download_image,
        name='tardis.tardis_portal.iiif.download_image'),
    url(r'^(?P<datafile_id>\d+)/(?P<region>[^\/]+)/(?P<size>[^\/]+)/'
        r'(?P<rotation>[\d\.]+)/(?P<quality>\w+).(?P<format>\w+)$',
        download_image,
        name='tardis.tardis_portal.iiif.download_image'),
    url(r'^(?P<datafile_id>\d+)/info.(?P<format>\w+)$', download_info,
        name='tardis.tardis_portal.iiif.download_info'),
]

datafile_urls = [
    url(r'^view/(?P<datafile_id>\d+)/$',
        view_datafile,
        name='tardis.tardis_portal.download.view_datafile'),
    url(r'^iiif/', include(iiif_urls)),
]
