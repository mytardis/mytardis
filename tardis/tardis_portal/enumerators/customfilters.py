"""Enumerator to hold the key terms for custom filters for apps
"""

from enum import Enum


class CustomFilters(str, Enum):
    """Enumerator to hold the string values for filtering"""

    IDENTIFIERS = "identifier"
