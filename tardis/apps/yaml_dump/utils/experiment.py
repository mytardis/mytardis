"""utils.experiment.py

A set of functions to wrangle the data into an appropriate format for export via YAML

Author: Chris Seal <c.seal@auckland.ac.nz>
"""
import contextlib
from typing import Any, Dict

from django.conf import settings

from tardis.apps.yaml_dump.models.experiment import Experiment
from tardis.apps.yaml_dump.utils.utility import (
    add_acls_to_dataclass,
    add_data_classification_to_dataclass,
    add_metadata_to_dataclass,
)

INGESTED = 5


# TODO: https://aucklanduni.atlassian.net/browse/IDS-686
def wrangle_experiment_into_IDW_YAML(experiment: Dict[str, Any]) -> Experiment:
    """Flatten the structure of an experiment into the format suited to dump to YAML

    Args:
        experiment (Dict[str,Any]): An experiment dictionary produced by the serializer

    Returns:
        Experiment: The YAML object representing an Experiment
    """
    experiment_dc = Experiment(
        data_status=INGESTED,
        description=experiment["description"],
        title=experiment["title"],
    )
    with contextlib.suppress(IndexError, KeyError):
        experiment_dc.object_schema = (
            experiment["experimentparameterset_set"][0]["schema"]["namespace"] or ""
        )
    # TODO: https://aucklanduni.atlassian.net/browse/IDS-685
    experiment_dc = add_metadata_to_dataclass(experiment_dc, experiment)
    experiment_dc = add_acls_to_dataclass(experiment_dc, experiment)
    experiment_dc = add_data_classification_to_dataclass(experiment_dc, experiment)

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = [value["identifier"] for value in experiment["identifiers"]]
        experiment_dc.identifiers = identifiers
    return experiment_dc
