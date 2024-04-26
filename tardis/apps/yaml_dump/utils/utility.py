"""Utility functions to help reduce repetition"""


import contextlib
from typing import Any, Dict, Union

from tardis.apps.dataclassification.decorators import DATA_CLASSIFICATION_ACTIVE
from tardis.apps.yaml_dump.models import Project
from tardis.apps.yaml_dump.models.access_control import GroupACL, UserACL
from tardis.apps.yaml_dump.models.dataset import Dataset
from tardis.apps.yaml_dump.models.experiment import Experiment
from tardis.apps.yaml_dump.models.username import Username


def add_data_classification_to_dataclass(
    dataclass: Union[Project, Experiment, Dataset], obj: Dict[str, Any]
) -> Union[Project, Experiment, Dataset]:
    if DATA_CLASSIFICATION_ACTIVE:
        dataclass.data_classification = obj["data_classification"]["classification"]
    return dataclass


def add_metadata_to_dataclass(
    dataclass: Union[Project, Experiment, Dataset], obj: Dict[str, Any]
) -> Union[Project, Experiment, Dataset]:
    metadata = {}
    if isinstance(dataclass, Project):
        parameterset_key = "projectparameterset_set"
    elif isinstance(dataclass, Experiment):
        parameterset_key = "experimentparameterset_set"
    elif isinstance(dataclass, Dataset):
        parameterset_key = "datasetparameterset_set"
    else:
        raise ValueError(
            "Dataclass should be a Projet, Experiment or Dataset as defined in the YAML app"
        )
    with contextlib.suppress(IndexError):
        with contextlib.suppress(KeyError):
            for parameter in obj[parameterset_key][0]["parameters"]:
                value = None
                if parameter["numerical_value"]:
                    value = parameter["numerical_value"]
                if parameter["string_value"]:
                    value = parameter["string_value"]
                if parameter["datetime_value"]:
                    value = parameter["datetime_value"]
                metadata[parameter["name"]["name"]] = value
    dataclass.metadata = metadata
    return dataclass


def add_acls_to_dataclass(
    dataclass: Union[Project, Experiment, Dataset], obj: Dict[str, Any]
) -> Union[Project, Experiment, Dataset]:
    user_acls = []
    group_acls = []
    with contextlib.suppress(KeyError):
        user_acls = [
            UserACL(
                user=Username(acl["user"]),
                is_owner=acl["is_owner"],
                can_download=acl["can_download"],
                see_sensitive=acl["see_sensitive"],
            )
            for acl in obj["user_acls"]
        ] or []
    dataclass.users = user_acls
    with contextlib.suppress(KeyError):
        group_acls = [
            GroupACL(
                group=acl["group"],
                is_owner=acl["is_owner"],
                can_download=acl["can_download"],
                see_sensitive=acl["see_sensitive"],
            )
            for acl in obj["group_acls"]
        ] or []
    dataclass.groups = group_acls
    return dataclass
