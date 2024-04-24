"""utils.experiment.py

A set of functions to wrangle the data into an appropriate format for export via YAML

Author: Chris Seal <c.seal@auckland.ac.nz>
"""
from typing import Any, Dict
from django.conf import settings

from tardis.apps.yaml_dump.models.experiment import Experiment
from tardis.apps.yaml_dump.utils.project import INGESTED

INGESTED = 5

def wrangle_experiment_into_IDW_YAML(experiment: Dict[str, Any]) -> Experiment:
    """Flatten the structure of an experiment into the format suited to dump to YAML
    
    Args:
        experiment (Dict[str,Any]): An experiment dictionary produced by the serializer
        
    Returns:
        Experiment: The YAML object representing an Experiment
    """