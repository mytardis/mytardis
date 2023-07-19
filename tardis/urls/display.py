"""
Display URLs
"""
from django.urls import re_path

from tardis.tardis_portal.views import (
    display_datafile_image,
    display_dataset_image,
    display_experiment_image,
    load_datafile_image,
    load_dataset_image,
    load_experiment_image,
)

display_urls = [
    re_path(
        r"^ExperimentImage/load/(?P<parameter_id>\d+)/$",
        load_experiment_image,
        name="tardis.tardis_portal.views.load_experiment_image",
    ),
    re_path(
        r"^DatasetImage/load/(?P<parameter_id>\d+)/$",
        load_dataset_image,
        name="tardis.tardis_portal.views.load_dataset_image",
    ),
    re_path(
        r"^DatafileImage/load/(?P<parameter_id>\d+)/$",
        load_datafile_image,
        name="tardis.tardis_portal.views.load_datafile_image",
    ),
    re_path(
        r"^ExperimentImage/(?P<experiment_id>\d+)/"
        "(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$",
        display_experiment_image,
        name="tardis.tardis_portal.views.display_experiment_image",
    ),
    re_path(
        r"^DatasetImage/(?P<dataset_id>\d+)/(?P<parameterset_id>\d+)/"
        "(?P<parameter_name>\w+)/$",
        display_dataset_image,
        name="tardis.tardis_portal.views.display_dataset_image",
    ),
    re_path(
        r"^DatafileImage/(?P<datafile_id>\d+)/"
        "(?P<parameterset_id>\d+)/(?P<parameter_name>\w+)/$",
        display_datafile_image,
        name="tardis.tardis_portal.views.display_datafile_image",
    ),
]
