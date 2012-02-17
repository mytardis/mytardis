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
transfer_service.py

.. moduleauthor:: Kieran Spear <kispear@gmail.com>
.. moduleauthor:: Shaun O'Keefe <shaun.okeefe.0@gmail.com>

"""
import logging
import os.path

from django.conf import settings

from tardis.tardis_portal.models import Experiment

logger = logging.getLogger(__file__)

#
# For watching over things on the provider side of the 
# sync operation. Not sure whether most of this could just
# be done in the object manager of the SyncedExperiment model
#

class TransferService:

    TRANSFER_COMPLETE = 1
    TRANSFER_IN_PROGRESS = 2
    TRANSFER_FAILED = 3

    statuses = (
            (TRANSFER_COMPLETE, 'Transfer Complete'),
            (TRANSFER_IN_PROGRESS, 'Transfer In Progress'),
            (TRANSFER_FAILED, 'Transfer Failed'),
            )

    # Exception classes
    SiteError = type('SiteError', (Exception,), {})
    TransferError = type('TransferError', (Exception,), {})
    InvalidUIDError = type('InvalidUIDError', (Exception,), {})


    def __init__(self, manager=None):
        if manager:
            self.manager = manager
        else:
            import managers
            self.manager = managers.manager()


    def start_file_transfer(self, uid, site_settings_url):
        return self.manager.start_file_transfer(uid, site_settings_url)


    def get_status(self, uid):
        # status_dict optionally contains 'message' and 'progress'
        (code, timestamp, status_dict) = self.manager.get_status(uid)

        status = status_dict
        try:
            status['status'] = filter(lambda s: s[0] == code, statuses)[0]
        except IndexError:
            return None
        status['timestamp'] = timestamp
        return status

