"""
Facility URLs
"""
from django.urls import re_path

from tardis.tardis_portal.views import (
    facility_overview,
    facility_overview_data_count,
    facility_overview_dataset_detail,
    facility_overview_experiments,
    facility_overview_facilities_list,
)

facility_urls = [
    re_path(
        r"^overview/$",
        facility_overview,
        name="tardis.tardis_portal.views.facility_overview",
    ),
    re_path(
        r"^fetch_data/(?P<facility_id>\d+)/count/",
        facility_overview_data_count,
        name="tardis.tardis_portal.views.facility_overview_data_count",
    ),
    re_path(
        r"^fetch_data/(?P<facility_id>\d+)/"
        r"(?P<start_index>\d+)/(?P<end_index>\d+)/$",
        facility_overview_experiments,
        name="tardis.tardis_portal.views.facility_overview_experiments",
    ),
    re_path(
        r"^fetch_datafiles/(?P<dataset_id>\d+)/$",
        facility_overview_dataset_detail,
        name="tardis.tardis_portal.views.facility_overview_dataset_detail",
    ),
    re_path(
        r"^fetch_facilities_list/$",
        facility_overview_facilities_list,
        name="tardis.tardis_portal.views.facility_overview_facilities_list",
    ),
]
