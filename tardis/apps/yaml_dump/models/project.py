from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from yaml import SafeLoader

from tardis.apps.yaml_dump.models.access_control import IAccessControl
from tardis.apps.yaml_dump.models.dataclassification import IDataClassification
from tardis.apps.yaml_dump.models.identifiers import IIdentifiers
from tardis.apps.yaml_dump.models.username import Username
from tardis.apps.yaml_dump.models.yaml_dataclass import YAMLDataclass


@dataclass
class Project(YAMLDataclass, IAccessControl, IDataClassification):
    """
    A class representing MyTardis Project objects.

    Attributes:
        name (str): The name of the project.
        description (str): A brief description of the project.
        identifiers (List[str]): A list of identifiers for the project.
        data_classification (DataClassification): The data classification of the project.
        principal_investigator (str): The name of the principal investigator for the project.
    """

    yaml_tag = "!Project"
    yaml_loader = SafeLoader
    description: str = ""
    name: str = ""
    data_status: int = 5
    principal_investigator: Username = field(
        default=Username(), metadata={"label": "Username"}
    )
    identifiers: list[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    object_schema: str = ""  # MTUrl in ingestion script
    # fields to add for updated data status
    created_by: Optional[str] = None
    institution: Optional[List[str]] = None
    start_time: Optional[datetime | str] = None
    end_time: Optional[datetime | str] = None
    embargo_until: Optional[datetime | str] = None
    delete_in_days: int = -1
    archive_in_days: int = 365
    url: Optional[str] = None
    _store: Optional["IngestionMetadata"] = field(repr=False, default=None)

    def __post_init__(self) -> None:
        self.identifiers_delegate = ProjectIdentifiers(self)


class ProjectIdentifiers(IIdentifiers):
    """Project-specific methods related to identifiers."""

    def __init__(self, project: Project):
        self.project = project
        super().__init__(project.identifiers)

    def _is_unique(self, id: str) -> bool:
        """Private method to check whether an id is unique across all
        Projects in the store.

        Args:
            id (str): The ID to check

        Returns:
            bool: True if the identifier is unique, False if not.
        """
        assert self.project._store is not None
        return not any(
            project.identifiers_delegate.has(id)
            for project in self.project._store.projects
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
        """Updates an existing identifier in this Project and
        all related Experiments in the store. Checks if the identifier
        is unique. Returns True if successful, False if not.

        Args:
            old_id (str): The ID to update
            id (str): The new ID.

        Returns:
            bool: True if successfully updated, False if not unique.
        """
        assert self.project._store is not None
        # Find all experiments and update their IDs.
        if not self._is_unique(id):
            # Check if the new ID is unique.
            return False
        for experiment in self.project._store.experiments:
            if old_id in experiment.projects:
                # Update the projects list with the new_id
                experiment.projects.remove(old_id)
                experiment.projects.append(id)

        return super().update(old_id, id)

    def delete(self, id_to_delete: str) -> bool:
        """Deletes an identifier in this Project,
        and updates identifiers in related objects to use
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
        assert self.project._store is not None
        for experiment in self.project._store.experiments:
            if id_to_delete in experiment.projects:
                # Replace id_to_delete with the new_id within projects list
                experiment.projects.remove(id_to_delete)
                experiment.projects.append(new_id)
        return True
