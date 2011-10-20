

from django.core.management.base import BaseCommand
from tardis.tardis_portal.models import Dataset_File
from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.models import DatafileParameter
from tardis.tardis_portal.models import DatafileParameterSet
from tardis.tardis_portal.models import ParameterName
from tardis.tardis_portal.models import Schema
from tardis.tardis_portal.models import DatasetParameter
from tardis.tardis_portal.models import DatasetParameterSet

from os import path
import re
from django.conf import settings

from fractions import Fraction


from tardis.tardis_portal.models import Experiment

import itertools

from tardis.apps.hpctardis.metadata import get_metadata
from tardis.apps.hpctardis.metadata import get_schema
from tardis.apps.hpctardis.metadata import save_metadata
from tardis.apps.hpctardis.metadata import go


class Command(BaseCommand):
    
    help = "help me"
    
  
    def handle(self, *args, **options):
        go()