# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2012, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2012, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
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
"""
models.py

.. moduleauthor:: Kieran Spear <kispear@gmail.com>
.. moduleauthor:: Shaun O'Keefe <shaun.okeefe.0@gmail.com>

"""
import json

from django.db import models
from django.dispatch import receiver
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.signals import received_remote
from tardis.apps.sync.consumer_fsm import ConsumerFSMField

import logging

logger = logging.getLogger(__file__)
#
# Maybe a common base class so we can turn anything into 
# a synced model?
#

class SyncedExperiment(models.Model):
    experiment = models.ForeignKey(Experiment)
    uid = models.TextField()
    state = ConsumerFSMField(default='Ingested') 
    #prev_state = ConsumerFSMField(default='Ingested')
    # Keep track of which provider this experiment came from.
    # This might be better as another table if there's more to store.
    provider_url = models.TextField()
    msg = models.TextField(default='')

    def is_complete(self):
        return self.state.is_final_state() 

    def progress(self):
        self.state = self.state.get_next_state(self)
        self.save()

    def status(self):
        try:
            return json.loads(self.msg)
        except ValueError:
            return None

    def save_status(self, status_dict):
        self.msg = json.dumps(status_dict)
        self.save()


@receiver(received_remote, sender=Experiment)
def experiment_received(sender, **kwargs):
    exp = kwargs['instance']
    uid = kwargs['uid']
    from_url = kwargs['from_url']
    logger.info('Sync app saw experiment %s' % uid)
    synced_exp = SyncedExperiment(experiment=exp, uid=uid, provider_url=from_url)
    synced_exp.save()

