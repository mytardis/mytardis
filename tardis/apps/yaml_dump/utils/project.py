"""utils.project.py

A set of functions to wrangle the data into an appropriate format for export via YAML
"""

from typing import Any, Dict

from django.conf import settings

from tardis.apps.yaml_dump.models.project import Project
from tardis.apps.yaml_dump.models.username import Username
from tardis.apps.yaml_dump.utils.utility import (
    add_acls_to_dataclass,
    add_data_classification_to_dataclass,
    add_metadata_to_dataclass,
)

INGESTED = 5


# TODO: https://aucklanduni.atlassian.net/browse/IDS-686
def wrangle_project_into_IDW_YAML(project: Dict[str, Any]) -> Project:
    """Flatten the structure of a project into the format suited to dump in a YAML

    Args:
        project (Dict[str,Any]): A project dictionary produced by the serializer

    Returns:
        Project: The YAML object representing the project
    """
    project_dc = Project(
        data_status=INGESTED,  # INGESTED flag is set since we can get the data from MyTardis
        description=project["description"],
        name=project["name"],
        principal_investigator=Username(
            f'{project["principal_investigator"]["username"]}',
        ),
    )
    project_dc.object_schema = (
        project["experimentparameterset_set"][0]["schema"]["namespace"] or ""
    )
    # TODO: https://aucklanduni.atlassian.net/browse/IDS-685
    project_dc = add_metadata_to_dataclass(project_dc, project)
    project_dc = add_acls_to_dataclass(project_dc, project)
    project_dc = add_data_classification_to_dataclass(project_dc, project)

    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "project" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = [value["identifier"] for value in project["identifiers"]]
        project_dc.identifiers = identifiers
    return project_dc
