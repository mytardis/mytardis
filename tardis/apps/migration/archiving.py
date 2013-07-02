#
# Copyright (c) 2013, Centre for Microscopy and Microanalysis
#   (University of Queensland, Australia)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the University of Queensland nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
#


from urllib2 import Request, urlopen, HTTPError
from urlparse import urlparse
from tempfile import TemporaryFile
import os

from django.conf import settings
from django.db import transaction

from tardis.tardis_portal.fetcher import get_privileged_opener
from tardis.tardis_portal.staging import stage_replica
from tardis.tardis_portal.util import generate_file_checksums

from tardis.apps.migration import MigrationError
from tardis.tardis_portal.models import \
    Experiment, Dataset, Dataset_File, Replica 

import logging

logger = logging.getLogger(__name__)

def create_experiment_archive(exp, outfile):
    with TemporaryFile as manifest, \
            TarFile(mode='w|gz', fileobj=outfile) as tarfile:
        MetsExporter.export_to_file(exp, manifest)
        tarfile.add(manifest.name, arcname='Manifest')
        for datafile in exp.get_datafiles():
            
        

def remove_experiment(exp):
    pass

def remove_experiment_data(exp):
    pass

def create_archive_record(exp, url):
    pass

