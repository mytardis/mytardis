from dataclasses import dataclass, field
from typing import List, Optional

from yaml import SafeLoader

from tardis.apps.yaml_dump.models.username import Username
from tardis.apps.yaml_dump.models.yaml_dataclass import YAMLDataclass


@dataclass
class UserACL(YAMLDataclass):
    """Model to define user access control. This differs from the group
    access control in that it validates the username against a known regex.
    """

    yaml_tag = "!UserACL"
    yaml_loader = SafeLoader
    user: Username = field(default=Username(), metadata={"label": "Username"})
    is_owner: bool = field(default=False, metadata={"label": "Is owner?"})
    can_download: bool = field(default=False, metadata={"label": "Can download?"})
    see_sensitive: bool = field(default=False, metadata={"label": "See sensitive?"})


@dataclass
class GroupACL(YAMLDataclass):
    """Model to define group access control."""

    yaml_tag = "!GroupACL"
    yaml_loader = SafeLoader
    group: str = field(default="", metadata={"label": "Group ID"})
    is_owner: bool = field(default=False, metadata={"label": "Is owner?"})
    can_download: bool = field(default=False, metadata={"label": "Can download?"})
    see_sensitive: bool = field(default=False, metadata={"label": "See sensitive?"})


@dataclass
class IAccessControl:
    """
    A class representing fields related to access
    control.
    When set to None, the fields represent that they are inheriting
    access control fields from the Project, Experiment or Dataset higher up
    in the hierarchy.
    """

    users: Optional[List[UserACL]] = None
    groups: Optional[List[GroupACL]] = None
