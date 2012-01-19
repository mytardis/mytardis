# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, RMIT e-Research Office
#   (RMIT University, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of RMIT University nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
extractmetadata.py

.. moduleauthor:: Ian Thomas <Ian.Edward.Thomas@rmit.edu.au>

"""

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
            yesno = raw_input("Are you REALLY sure you want to extract ALL "
                              "experiment metadata (will overwrite existing "
                              "data) [y/N]")
            if yesno.lower() == "y":    
                process_all_experiments()
        else:
            try:
                expid = int(args[0])
            except ValueError: 
                self.stderr.write("invalid experiment id")
                return
            exp = Experiment.objects.get(id=expid)    
            process_experimentX(exp)