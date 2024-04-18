"""utils.project.py

A set of functions to wrangle the data into an appropriate format for export via YAML
"""
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, List

from django.conf import settings
from tardis.apps.yaml_dump.utils.common_models import UsernameYAMLDataclass

INGESTED = 5

@dataclass
class ProjectYAMLDataclass:
    data_status: int
    description: str
    name: str
    object_schema: str
    principal_investigator: str
    metadata: Optional[List[Dict[str, Any]]] = None
    data_classification: Optional[int] = None
    identifiers: Optional[List[str]] = None


def wrangle_project_into_IDW_YAML(project: Dict[str, Any]) -> ProjectYAMLDataclass:
    """Flatten the structure data into the format suited to dump in a YAML

    Args:
        project (Dict[str,Any]): A project dictionary produced by the serializer

    Returns:
        ProjectYAMLDataclass: The flattened dictionary
    """
    return_dc = ProjectYAMLDataclass(
        data_status = INGESTED,  # INGESTED flag is set since we can get the data from MyTardis
        description = project["description"],
        name = project["name"],
        object_schema = project["projectparameterset_set"][0]["schema"]["namespace"],
        principal_investigator = f'{project["principal_investigator"]["username"]}',
    )
    if project['projectparameterset_set'][0]['parameters']:
        metadata = []
        for parameter in project['projectparameterset_set'][0]['parameters']:
            value = None
            if parameter['numerical_value']:
                value = parameter['numerical_value']
            if parameter['string_value']:
                value = parameter['string_value']
            if parameter['datetime_value']:
                value = parameter['datetime_value']
            metadata.append({parameter['name']['name']:value})
        return_dc.metadata = metadata

    if "tardis.apps.dataclassification" in settings.INSTALLED_APPS:
        return_dc.data_classification = project["data_classification"]["classification"]
    if (
        "tardis.apps.identifiers" in settings.INSTALLED_APPS
        and "project" in settings.OBJECTS_WITH_IDENTIFIERS
    ):
        identifiers = []
        for value in project["identifiers"]:
            identifiers.append(value["identifier"])
        return_dc.identifiers = identifiers
    return return_dc
        
def project_representer(dumper, data):
    return dumper.represent_mapping("!Project", asdict(data))

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
