from typing import TypeAlias

from tardis.apps.yaml_dump.models.datafile import Datafile
from tardis.apps.yaml_dump.models.dataset import Dataset
from tardis.apps.yaml_dump.models.experiment import Experiment
from tardis.apps.yaml_dump.models.project import Project
from tardis.apps.yaml_dump.utils.yaml_helpers import initialise_yaml_helpers

MyTardisObject: TypeAlias = Project | Experiment | Dataset | Datafile

initialise_yaml_helpers()
