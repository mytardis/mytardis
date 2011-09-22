# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2011, RMIT e-Research Office
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
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
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

import logging
from django.http import HttpResponse
from tardis.tardis_portal.shortcuts import render_response_index
from django.views.decorators.cache import never_cache
from django.conf import settings

from django.template import Context

from tardis.tardis_portal.views import authz
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.shortcuts import return_response_error

from tardis.apps.hpctardis.publish.RMITANDSService import RMITANDSService

logger = logging.getLogger(__name__)

def test(request):
    return HttpResponse(render_response_index(request,
                                              'hpctardis/test.html'))
    
@never_cache
@authz.experiment_ownership_required
def publish_experiment(request, experiment_id):
    """
    Make the experiment open to public access.
    Sets off a chain of PublishProvider modules for
    extra publish functionality.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be published
    :type experiment_id: string

    """
    import os

    logger.debug("started publish")
    experiment = Experiment.objects.get(id=experiment_id)
    username = str(request.user).partition('_')[2]

        
    publishService = RMITANDSService(experiment.id)
    logger.debug("made service")
 

    if request.method == 'POST':  # If the form has been submitted...

    
        legal = True
        success = True
    
            
        context_dict = {}
        #fix this slightly dodgy logic
        context_dict['publish_result'] = "submitted"
        if 'legal' in request.POST:
            experiment.public = True
            experiment.save()

            context_dict['publish_result'] = \
            publishService.execute_publishers(request)

            for result in context_dict['publish_result']:
                if not result['status']:
                    success = False

        else:
            logger.debug('Legal agreement for exp: ' + experiment_id +
            ' not accepted.')
            legal = False

        # set dictionary to legal status and publish success result
        context_dict['legal'] = legal
        context_dict['success'] = success
    else:
        TARDIS_ROOT = os.path.abspath(\
        os.path.join(os.path.dirname(__file__)))

        legalpath = os.path.join(TARDIS_ROOT,
                      "publish/legal.txt")

        # if legal file isn't found then we can't proceed
        try:
            legalfile = open(legalpath, 'r')
        except IOError:
            logger.error('legal.txt not found. Publication halted.')
            return return_response_error(request)

        legaltext = legalfile.read()
        legalfile.close()
        logger.debug("templatepaths=%s" % publishService.get_template_paths())
        context_dict = \
        {'username': username,
        'publish_forms': publishService.get_template_paths(),
        'experiment': experiment,
        'legaltext': legaltext,
        }

        context_dict = dict(context_dict, \
        **publishService.get_contexts(request))

    c = Context(context_dict)
    return HttpResponse(render_response_index(request,
                        'tardis_portal/publish_experiment.html', c))
    
    
    
def rif_cs(request):
    """
    Display rif_cs of collection / parties / acitivies
    This function is highly dependent on production requirements

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`

    """

    #currently set up to work with EIF038 dummy data

    experiments = Experiment.objects.filter(public=True)
    import datetime
    c = Context({
            'experiments': experiments,
            'now': datetime.datetime.now(),
            'party_rif_cs': None,
            'activity_rif_cs': None,
        })
    return HttpResponse(render_response_index(request,\
        'rif_cs_profile/rif-cs.xml', c),
        mimetype='application/xml')
   
