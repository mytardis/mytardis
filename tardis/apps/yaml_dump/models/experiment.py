from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from yaml import SafeLoader

from tardis.apps.yaml_dump.models.access_control import IAccessControl
from tardis.apps.yaml_dump.models.dataclassification import IDataClassification
from tardis.apps.yaml_dump.models.identifiers import IIdentifiers
from tardis.apps.yaml_dump.models.yaml_dataclass import YAMLDataclass


@dataclass
class Experiment(YAMLDataclass, IAccessControl, IDataClassification):
    """
    A class representing MyTardis Experiment objects.
    """

    yaml_tag = "!Experiment"
    yaml_loader = SafeLoader
    title: str = ""
    data_status: int = 5
    projects: List[str] = field(default_factory=list)
    description: str = ""
    identifiers: list[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    object_schema: str = ""  # MTUrl in ingestion script
    # fields to add for updated data status
    institution_name: Optional[str] = None
    created_by: Optional[str] = None
    url: Optional[str] = None  # MTUrl in ingestion script
    locked: bool = False
    start_time: Optional[datetime | str] = None
    end_time: Optional[datetime | str] = None
    created_time: Optional[datetime | str] = None
    update_time: Optional[datetime | str] = None
    embargo_until: Optional[datetime | str] = None
    _store: Optional["IngestionMetadata"] = field(repr=False, default=None)

    def __post_init__(self) -> None:
        self.identifiers_delegate = ExperimentIdentifiers(self)


class ExperimentIdentifiers(IIdentifiers):
    """Experiment-specific methods related to identifiers."""

    def __init__(self, experiment: Experiment):
        self.experiment = experiment
        super().__init__(experiment.identifiers)

    def _is_unique(self, id: str) -> bool:
        """Private method to check whether an id is unique across all
        Projects in the store.

        Args:
            id (str): The ID to check

        Returns:
            bool: True if the identifier is unique, False if not.
        """
        assert self.experiment._store is not None
        return not any(
            experiment.identifiers_delegate.has(id)
            for experiment in self.experiment._store.experiments
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
        """Updates an existing identifier in this Experiment and
        all related Datasets in the store. Checks if the identifier
        is unique. Returns True if successful, False if not.

        Args:
            old_id (str): The ID to update
            id (str): The new ID.

        Returns:
            bool: True if successfully updated, False if not unique.
        """
        assert self.experiment._store is not None
        # Find all datasets and update their IDs.
        if not self._is_unique(id):
            # Check if the new ID is unique.
            return False
        for dataset in self.experiment._store.datasets:
            if old_id in dataset.experiments:
                dataset.experiments.remove(old_id)
                dataset.experiments.append(id)
        return super().update(old_id, id)

    def delete(self, id_to_delete: str) -> bool:
        """Deletes an identifier in this Experiment,
        and updates identifiers in related Datasets to use
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
        assert self.experiment._store is not None
        for dataset in self.experiment._store.datasets:
            if id_to_delete in dataset.experiments:
                dataset.experiments.remove(id_to_delete)
                dataset.experiments.append(new_id)
        return True
