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
metadata.py

.. moduleauthor:: Ian Thomas <Ian.Edward.Thomas@rmit.edu.au>

"""
from django.core.management.base import BaseCommand, CommandError
from tardis.tardis_portal.models import Experiment

from tardis.apps.hpctardis.views import _promote_experiments_to_public
from tardis.apps.hpctardis.models import PublishAuthorisation

from tardis.apps.hpctardis.publish.RMITANDSService import send_request_email


class Command(BaseCommand):
    
    help = "Allows pending public exeriments to promoted, or allow new verification emails to be sent"
    
    def handle(self, *args, **options):
            
        if len(args) < 1:
            self.stdout.write("no command specified\n")
            return
        
        if args[0] == 'resend':
            # Resend all outstanding auth emails for experiments
            
            expid = args[1]
            
            try:
                exp = Experiment.objects.get(id=expid,public=False)
            except Experiment.DoesNotExist:
                self.stderr.write("pending experiment does not exist")
                return
            
            
            publish_auths= PublishAuthorisation.objects.filter(experiment=exp)
            
            for publish_auth in publish_auths:
                if publish_auth.status == PublishAuthorisation.PENDING_APPROVAL:
                    send_request_email(publish_auth.party_record,
                                    publish_auth.activity_record,expid)
                
            
                        
            self.stdout.write('done\n')
            
        elif args[0] == 'promote':
            # Check PublishAuthEvents and make experiment public if fully
            # approved
            expid = args[1]
            
            try:
                exp = Experiment.objects.get(id=expid)
            except Experiment.DoesNotExist:
                self.stderr.write("experiment does not exist")
                return
            
            message = _promote_experiments_to_public(exp)
            self.stdout.write('done')
            self.stdout.write("process reports: %s" % message)
            self.stdout.write("done")
            
        elif args[0] == "test":
            self.stdout.write('done\n')
        else:
            self.stdout.write("no command specified\n")
