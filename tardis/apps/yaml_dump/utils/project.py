"""utils.project.py

A set of functions to wrangle the data into an appropriate format for export via YAML
"""

from typing import Any, Dict

from django.conf import settings

from tardis.apps.yaml_dump.models.access_control import GroupACL, UserACL
from tardis.apps.yaml_dump.models.project import Project
from tardis.apps.yaml_dump.models.username import Username

INGESTED = 5


def wrangle_project_into_IDW_YAML(project: Dict[str, Any]) -> Project:
    """Flatten the structure of a project into the format suited to dump in a YAML

    Args:
        project (Dict[str,Any]): A project dictionary produced by the serializer

    Returns:
        Project: The YAML object representing the project
    """
    return_dc = Project(
        data_status=INGESTED,  # INGESTED flag is set since we can get the data from MyTardis
        description=project["description"],
        name=project["name"],
        object_schema=project["projectparameterset_set"][0]["schema"]["namespace"],
        principal_investigator=Username(
            f'{project["principal_investigator"]["username"]}',
        ),
    )
    if project["projectparameterset_set"][0]["parameters"]:
        metadata = {}
        for parameter in project["projectparameterset_set"][0]["parameters"]:
            value = None
            if parameter["numerical_value"]:
                value = parameter["numerical_value"]
            if parameter["string_value"]:
                value = parameter["string_value"]
            if parameter["datetime_value"]:
                value = parameter["datetime_value"]
            metadata[parameter["name"]["name"]] = value
        return_dc.metadata = metadata
    user_acls = [
        UserACL(
            user=Username(acl["user"]),
            is_owner=acl["is_owner"],
            can_download=acl["can_download"],
            see_sensitive=acl["see_sensitive"],
        )
        for acl in project["user_acls"]
    ]
    return_dc.users = user_acls

    group_acls = [
        GroupACL(
            group=acl["group"],
            is_owner=acl["is_owner"],
            can_download=acl["can_download"],
            see_sensitive=acl["see_sensitive"],
        )
        for acl in project["user_acls"]
    ]
    return_dc.groups = group_acls

    if "tardis.apps.dataclassification" in settings.INSTALLED_APPS:
        return_dc.data_classification = project["data_classification"]["classification"]
    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "project" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = [value["identifier"] for value in project["identifiers"]]
        return_dc.identifiers = identifiers
    return return_dc
