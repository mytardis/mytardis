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
import json
import urllib
import httplib2

from django.conf import settings
from django.core.urlresolvers import reverse

from tardis.tardis_portal.models import Experiment

logger = logging.getLogger(__file__)

#
# For watching over things on the provider side of the 
# sync operation. Not sure whether most of this could just
# be done in the object manager of the SyncedExperiment model
#

class TransferService(object):

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

    # Returns a transfer id, which at the moment is just the uid.
    # In the future we may need a specific 'transfer id'
    # if experiments are being pushed to multiple institutions.
    def start_file_transfer(self, uid, site_settings_url, dest_path):
        return self.manager.start_file_transfer(uid, site_settings_url, dest_path)

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

    def push_experiment_to_institutions(self, experiment, owners):
        self.manager.push_experiment_to_institutions(experiment, owners)


class HttpClient(object):
    def _request(self, url, method, headers, data):
        body = None
        if data:
            body = urllib.urlencode(data)
        headers = {'Content-type': 'application/json'}
        h = httplib2.Http()
        resp, content = h.request(url, method, headers=headers, body=body)
        return (resp, content)

    def get(self, url, headers={}, data={}):
        return self._request(url, 'GET', headers, data)

    def post(self, url, headers={}, data={}):
        return self._request(url, 'POST', headers, data)


class TransferClient(object):
    client = HttpClient

    def __init__(self):
        self.client = TransferClient.client()

    def request_file_transfer(self, synced_exp):
        logger.debug('=== sending file request')
        from_url = synced_exp.provider_url
        # This could differ from institution to institution, so a better method
        # of setting the right path is probably needed.
        dest_file_path = str(synced_exp.experiment.id)
        # This reverse assumes that the urlpatterns are the same at each end.
        # It might be better if the from_url pointed directly to the file transfer
        # view, so we don't need to guess.
        url = from_url + reverse('sync-get-experiment')
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        data['uid'] = synced_exp.uid
        data['dest_path'] = dest_file_path
        data['site_settings_url'] = settings.MYTARDIS_SITE_URL \
                + reverse('tardis-site-settings')
        resp, content = self.client.post(url, headers=headers, data=data)
        if resp.status != 200:
            logger.error('File transfer request to %s failed: %s' % (url, resp.reason))

        return resp.status == 200

    def get_status(self, synced_exp):
        url = synced_exp.provider_url \
                + reverse('sync-transfer-status', args=[synced_exp.uid])
        resp, content = self.client.get(url)
        if resp.status == 200:
            return json.loads(content)
        logger.warning('Status request to %s failed: %s' % (url, resp.reason))
        return {
            'status': TransferService.TRANSFER_FAILED,
            'error': 'HTTP error: %s' % resp.reason
            }

