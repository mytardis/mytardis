from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from yaml import dump_all

from tardis.apps.yaml_dump.models.datafile import Datafile
from tardis.apps.yaml_dump.models.dataset import Dataset
from tardis.apps.yaml_dump.models.experiment import Experiment
from tardis.apps.yaml_dump.models.project import Project


@dataclass
class IngestionMetadata:
    """
    A class representing a collection of metadata, with
    objects of different MyTardis types. It can be serialised
    to become a YAML file for ingestion into MyTardis.
    """

    # A list of objects of each type.
    projects: List[Project] = field(default_factory=list)
    experiments: List[Experiment] = field(default_factory=list)
    datasets: List[Dataset] = field(default_factory=list)
    datafiles: List[Datafile] = field(default_factory=list)
    # Ingestion metadata file location
    file_path: Optional[Path] = None

    def is_empty(self) -> bool:
        """Returns whether there are any projects, experiments,
        datasets and datafiles.

        Returns:
            bool: True if there are, False if not.
        """
        return (
            len(self.projects) == 0
            and len(self.experiments) == 0
            and len(self.datasets) == 0
            and len(self.datafiles) == 0
        )

    def _to_yaml(self) -> str:
        """
        Returns a string of the YAML representation of the metadata.
        """
        concatenated: List[Any] = self.projects.copy()
        concatenated.extend(self.experiments)
        concatenated.extend(self.datasets)
        concatenated.extend(self.datafiles)
        yaml_file = dump_all(concatenated)
        return yaml_file

    def get_files_by_dataset(self, dataset: Dataset) -> List[Datafile]:
        """
        Returns datafiles that belong to a dataset.
        """
        all_files: List[Datafile] = []
        for file in self.datafiles:
            if not dataset.identifiers_delegate.has(file.dataset):
                continue
            # Concatenate list of fileinfo matching dataset
            # with current list
            all_files.append(file)
        return all_files

    def get_datasets_by_experiment(self, exp: Experiment) -> List[Dataset]:
        """
        Returns datasets that belong to a experiment.
        """
        all_datasets: List[Dataset] = []
        for dataset in self.datasets:
            # Check if any dataset experiment ids match experiment identifiers
            if not exp.identifiers_delegate.has(dataset.experiments):
                continue
            all_datasets.append(dataset)
        return all_datasets

    def get_experiments_by_project(self, proj: Project) -> List[Experiment]:
        """
        Returns experiments that belong to a project.
        """
        all_exps: List[Experiment] = []
        for exp in self.experiments:
            if not proj.identifiers_delegate.has(exp.projects):
                continue
            all_exps.append(exp)
        return all_exps
