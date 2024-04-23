from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DataStatus(Enum):
    """An enumerator for data status.
    Gaps have been left deliberately in the enumeration to allow for intermediate
    status of data that may arise.
    """

    READY_FOR_INGESTION = 1
    INGESTED = 5


@dataclass
class IDataStatus:
    """
    Common interface for MyTardis models with data statud labels.
    """

    data_status: Optional[DataStatus] = None
