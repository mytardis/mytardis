from enum import Enum


class AppList(str, Enum):
    """Enumerator to hold list of apps"""

    DATA_CLASSIFICATION = "tardis.apps.dataclassification"
    IDENTIFIERS = "tardis.apps.identifiers"
    PROJECTS = "tardis.apps.projects"
    SEARCH = "tardis.apps.search"
