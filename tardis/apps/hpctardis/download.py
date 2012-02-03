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
download.py override for hpctardis

.. moduleauthor::  Ian Thomas <Ian.Edward.Thomas@rmit.edu.au>

"""

import logging
import subprocess
import urllib
from os import path

from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseNotFound
from django.conf import settings

from tardis.tardis_portal.models import *

from tardis.tardis_portal.views import return_response_not_found, \
    return_response_error
    
from django.template import Context
from tardis.tardis_portal.staging import get_full_staging_path
from tardis.tardis_portal.shortcuts import render_response_index

from tardis.tardis_portal.auth.decorators import experiment_access_required as tardis_experiment_access_required
from tardis.tardis_portal.download import download_datafile as tardis_download_datafile
from tardis.tardis_portal.download import download_datafile_ws as tardis_download_datafile_ws
from tardis.tardis_portal.download import download_experiment
from tardis.tardis_portal.download import download_datafiles as tardis_download_datafiles



logger = logging.getLogger(__name__)


def return_response_datafile_private(request,exp):
    c = Context({'exp_id':exp.id,
                 'exp_name':exp.title,
                 'owner_name':exp.created_by.get_full_name(),
                 'owner_email': exp.created_by.email})
    return HttpResponseNotFound(render_response_index(request,
                                'hpctardis/contact_download.html', c))


def download_datafile(request, datafile_id):

    datafile = Dataset_File.objects.get(pk=datafile_id)
    exp = datafile.dataset.experiment
    
    if settings.PRIVATE_DATAFILES and exp.public:
        return return_response_datafile_private(request,exp)                   
    else:
        return tardis_download_datafile(request, datafile_id)
    

def download_datafile_ws(request):
    
    if 'url' in request.GET and len(request.GET['url']) > 0:
        url = urllib.unquote(request.GET['url'])
        raw_path = url.partition('//')[2]
        experiment_id = request.GET['experiment_id']
        datafile = Dataset_File.objects.filter(
                                url__endswith=raw_path,
                                dataset__experiment__id=experiment_id)[0]
        exp = datafile.dataset.experiment
        if settings.PRIVATE_DATAFILES and exp.public:
            return return_response_datafile_private(request,exp)                   
        else:
            return tardis_download_datafile_ws(request)        
    else:
        return return_response_error(request)
    
def download_experiment_alt(request, experiment_id, comptype):
    """
    takes string parameter "comptype" for compression method.
    Currently implemented: "zip" and "tar"
    """
    experiment = Experiment.objects.get(pk=experiment_id)    
    if settings.PRIVATE_DATAFILES and experiment.public:
        return return_response_datafile_private(request,experiment)                   
    else:    
        return  download_experiment(request, experiment_id=experiment_id, comptype=comptype)


def download_datafiles(request):
    expid = request.POST['expid']
    experiment = Experiment.objects.get(pk=expid)    
    if settings.PRIVATE_DATAFILES and experiment.public:
        return return_response_datafile_private(request,experiment)                   
    else:
        return tardis_download_datafiles(request)
