'''
Facility URLs
'''
from django.conf.urls import url

from tardis.tardis_portal.views import (
    facility_overview,
    facility_overview_data_count,
    facility_overview_experiments,
    facility_overview_dataset_detail,
    facility_overview_facilities_list
)

facility_urls = [
    url(r'^overview/$', facility_overview,
        name='tardis.tardis_portal.views.facility_overview'),
    url(r'^fetch_data/(?P<facility_id>\d+)/count/', facility_overview_data_count,
        name='tardis.tardis_portal.views.facility_overview_data_count'),
    url(r'^fetch_data/(?P<facility_id>\d+)/'
        r'(?P<start_index>\d+)/(?P<end_index>\d+)/$',
        facility_overview_experiments,
        name='tardis.tardis_portal.views.facility_overview_experiments'),
    url(r'^fetch_datafiles/(?P<dataset_id>\d+)/$',
        facility_overview_dataset_detail,
        name='tardis.tardis_portal.views.facility_overview_dataset_detail'),
    url(r'^fetch_facilities_list/$', facility_overview_facilities_list,
        name='tardis.tardis_portal.views.facility_overview_facilities_list'),
]
