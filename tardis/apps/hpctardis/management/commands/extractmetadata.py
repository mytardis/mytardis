

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

from tardis.apps.hpctardis.metadata import process_all_experiments
from tardis.apps.hpctardis.metadata import process_experimentX



class Command(BaseCommand):
    
    help = "Extracts metadata for given experiment, or all experiments"
     
    def handle(self, *args, **options):
        if len(args) < 1:
            self.stdout.write("no command specified\n")
            return
        
        if args[0] == 'all':
            process_all_experiments()
        else:
            try:
                expid = int(args[0])
            except ValueError: 
                self.stderr.write("invalid experiment")
                return
            exp = Experiment.objects.get(id=expid)    
            process_experimentX(exp)