from dataclasses import dataclass
from typing import Optional


@dataclass
class IDataClassification:
    """
    Common interface for MyTardis models with data classification labels.
    """

    data_classification: Optional[int] = None
