from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from yaml import SafeLoader

from tardis.apps.yaml_dump.models.access_control import IAccessControl
from tardis.apps.yaml_dump.models.yaml_dataclass import YAMLDataclass


@dataclass
class Datafile(YAMLDataclass, IAccessControl):
    """
    A class representing MyTardis Datafile objects.
    """

    yaml_tag = "!Datafile"
    yaml_loader = SafeLoader
    filename: str = ""
    data_status: int = 5
    directory: Path = field(default_factory=Path)
    # This is for temporarily storing the absolute path,
    # required for generating relative path when saving.
    path_abs: Path = field(repr=False, default_factory=Path)
    size: float = 0
    md5sum: str = ""
    mimetype: str = ""
    dataset: str = ""
    metadata: Optional[Dict[str, Any]] = None
    object_schema: str = ""  # MTUrl in ingestion script
    _store: Optional["IngestionMetadata"] = field(repr=False, default=None)

    def __getstate__(self) -> dict[str, Any]:
        """Override method for pyyaml's serialisation method,
        where we check if metadata is empty. If empty, we return
        None, because the ingestion script expects either a None
        or a dictionary with entries.

        Returns:
            dict[str, Any]: The state of the Datafile for serialisation.
        """
        file_state = super().__getstate__()
        if self.metadata is not None and len(self.metadata) == 0:
            # If metadata is an empty dict, then replace with a None.
            file_state["metadata"] = None
        return file_state
