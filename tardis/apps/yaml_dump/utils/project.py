"""utils.project.py

A set of functions to wrangle the data into an appropriate format for export via YAML
"""

from typing import Any, Dict

from django.conf import settings

INGESTED = 5


def wrangle_project_into_IDW_YAML(project: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten the structure data into the format suited to dump in a YAML

    Args:
        project (Dict[str,Any]): A project dictionary produced by the serializer

    Returns:
        Dict[str,Any]: The flattened dictionary
    """
    return_dict = {
        "data_status": INGESTED,  # INGESTED flag is set since we can get the data from MyTardis
        "description": project["description"],
        "name": project["name"],
        "object_schema": project["parameterset"][0]["schema"]["namespace"],
        "principal_investigator": project["principal_investigator"]["username"],
    }
    if "tardis.apps.dataclassification" in settings.INSTALLED_APPS:
        return_dict["data_classification"] = project["dataclassification"]
    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "project" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        return_dict["identifiers"] = project["identifiers"]


"""
    !Project
data_classification: null
data_status: null
description: ''
groups: []
identifiers:
- helen-project
metadata: null
name: Helen's project
object_schema: ''
principal_investigator: !Username 'szen012'
users: []"""
