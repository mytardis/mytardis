from dataclasses import dataclass
from enum import Enum
from typing import Optional

class DataClassification(Enum):
    """An enumerator for data classification.
    Gaps have been left deliberately in the enumeration to allow for intermediate
    classifications of data that may arise. The larger the integer that the classification
    resolves to, the less sensitive the data is.
    """

    RESTRICTED = 1
    SENSITIVE = 25
    INTERNAL = 100
    PUBLIC = 100


@dataclass
class IDataClassification:
    """
    Common interface for MyTardis models with data classification labels.
    """

    data_classification: Optional[DataClassification] = None