"""A set of enumerators relating to the Data Classification App.
"""

from enum import Enum


class DataClassificationEnum(Enum):
    RESTRICTED = 0
    SENSITIVE = 25
    INTERNAL = 50
    PUBLIC = 100


class DataClassificationAppEnum(Enum):
    NAME = "tardis.apps.dataclassification"
    VERBOSE_NAME = "dataclassification"