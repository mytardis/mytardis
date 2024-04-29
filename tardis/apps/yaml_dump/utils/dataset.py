"""A set of functions to wrangle the data into an appropriate format for export via YAML"""

import contextlib
from typing import Any, Dict

from django.conf import settings

from tardis.apps.yaml_dump.models.dataset import Dataset
from tardis.apps.yaml_dump.utils.utility import (
    add_acls_to_dataclass,
    add_data_classification_to_dataclass,
    add_metadata_to_dataclass,
)

INGESTED = 5


# TODO: https://aucklanduni.atlassian.net/browse/IDS-686
def wrangle_dataset_into_IDW_YAML(dataset: Dict[str, Any]) -> Dataset:
    """Flatten the structure of an dataset into the format suited to dump to YAML

    Args:
        dataset (Dict[str,Any]): A dataset dictionary produced by the serializer

    Returns:
        Dataset: The YAML object representing a Dataset
    """
    dataset_dc = Dataset(
        data_status=INGESTED,
        description=dataset["description"],
    )
    with contextlib.suppress(IndexError, KeyError):
        dataset_dc.object_schema = (
            dataset["datasetparameterset_set"][0]["schema"]["namespace"] or ""
        )
    # TODO: https://aucklanduni.atlassian.net/browse/IDS-685
    dataset_dc = add_metadata_to_dataclass(dataset_dc, dataset)
    dataset_dc = add_acls_to_dataclass(dataset_dc, dataset)
    dataset_dc = add_data_classification_to_dataclass(dataset_dc, dataset)

    experiments = dataset["experiments"]
    dataset_dc.experiments = [
        experiment["identifiers"][0]["identifier"]
        if (
            "tardis.apps.identifiers" in settings.INSTALLED_APPS
            and "experiment" in settings.OBJECTS_WITH_IDENTIFIERS
            and experiment["identifiers"]
        )
        else experiment["name"]
        for experiment in experiments
    ]

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "dataset" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = [value["identifier"] for value in dataset["identifiers"]]
        dataset_dc.identifiers = identifiers
    return dataset_dc
