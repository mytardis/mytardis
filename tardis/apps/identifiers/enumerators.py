"""Enumerator to hold Idenfier specific values.
"""
from enum import Enum


class IdentifierObjects(str, Enum):
    INSTITUTION = "institution"
    PROJECT = "project"
    DATASET = "dataset"
    EXPERIMENT = "experiment"
    FACILITY = "facility"
    INSTRUMENT = "instrument"
