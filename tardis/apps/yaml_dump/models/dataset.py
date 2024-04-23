from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from yaml import SafeLoader

from tardis.apps.yaml_dump.models.access_control import IAccessControl
from tardis.apps.yaml_dump.models.dataclassification import IDataClassification
from tardis.apps.yaml_dump.models.datastatus import IDataStatus
from tardis.apps.yaml_dump.models.identifiers import IIdentifiers
from tardis.apps.yaml_dump.models.yaml_dataclass import YAMLDataclass


@dataclass
class Dataset(YAMLDataclass, IAccessControl, IDataClassification, IDataStatus):
    """
    A class representing MyTardis Dataset objects.
    """

    yaml_tag = "!Dataset"
    yaml_loader = SafeLoader
    description: str = ""
    experiments: List[str] = field(default_factory=list)
    instrument: str = ""
    identifiers: list[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    object_schema: str = ""  # MTUrl in ingestion script
    # fields to add for updated data status
    directory: Optional[Path] = None
    immutable: bool = False
    created_time: Optional[datetime | str] = None
    modified_time: Optional[datetime | str] = None
    _store: Optional["IngestionMetadata"] = field(repr=False, default=None)

    def __post_init__(self) -> None:
        """Dataclass lifecycle method that runs after an object is initialised.
        This method initialises the identifier delegate class for this model."""
        self.identifiers_delegate = DatasetIdentifiers(self)


class DatasetIdentifiers(IIdentifiers):
    """Dataset-specific methods related to identifiers."""

    def __init__(self, dataset: Dataset):
        self.dataset = dataset
        super().__init__(dataset.identifiers)

    def _is_unique(self, id: str) -> bool:
        """Private method to check whether an id is unique across all
        Projects in the store.

        Args:
            id (str): The ID to check

        Returns:
            bool: True if the identifier is unique, False if not.
        """
        assert self.dataset._store is not None
        return not any(
            dataset.identifiers_delegate.has(id)
            for dataset in self.dataset._store.datasets
        )

    def add(self, value: str) -> bool:
        """Adds a new identifier after checking
        if it's unique. Returns True if successfully added,
        returns False if it's not unique.

        Args:
            value (str): The new identifier.

        Returns:
            bool: Whether adding was successful.
        """
        return super().add(value) if self._is_unique(value) else False

    def update(self, old_id: str, id: str) -> bool:
        """Updates an existing identifier in this Dataset and
        all related Datafiles in the store. Checks if the identifier
        is unique. Returns True if successful, False if not.

        Args:
            old_id (str): The ID to update
            id (str): The new ID.

        Returns:
            bool: True if successfully updated, False if not unique.
        """
        assert self.dataset._store is not None
        if not self._is_unique(id):
            return False
        # Find all experiments and update their IDs.
        for datafile in self.dataset._store.datafiles:
            if datafile.dataset == old_id:
                datafile.dataset = id
        return super().update(old_id, id)

    def delete(self, id_to_delete: str) -> bool:
        """Deletes an identifier in this Dataset,
        and updates identifiers in related Datafiles to use
        an alternative identifier.
        Returns True if successfully deleted and updated, False if
        there are no other identifiers to use for related objects.

        Args:
            id_to_delete (str): The identifier to delete.

        Returns:
            bool: True if successfully deleted, False if unable
            to delete.
        """
        if self.identifiers is None:
            return False
        if len(self.identifiers) <= 1:
            return False
        super().delete(id_to_delete)
        new_id = self.first()
        assert self.dataset._store is not None
        for datafile in self.dataset._store.datafiles:
            if datafile.dataset == id_to_delete:
                datafile.dataset = new_id
        return True
