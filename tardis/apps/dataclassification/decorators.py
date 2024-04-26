"""Decorators that can be used with the API and related functions to check if the Data 
Classification app is being used.

Author: Chris Seal <c.seal@auckland.ac.nz> - 2024
"""

from django.conf import settings
#from functools import wraps
from tardis.apps.dataclassification.enumerators import DataClassificationAppEnum

DATA_CLASSIFICATION_ACTIVE = DataClassificationAppEnum.NAME.value in settings.INSTALLED_APPS

