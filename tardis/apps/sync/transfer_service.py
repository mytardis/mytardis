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
import json
import urllib
import httplib2

from django.conf import settings
from django.core.urlresolvers import reverse

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
    TRANSFER_BAD_REQUEST = 4
    TRANSFER_SERVER_ERROR = 5

    statuses = (
            (TRANSFER_COMPLETE, 'Transfer Complete'),
            (TRANSFER_IN_PROGRESS, 'Transfer In Progress'),
            (TRANSFER_FAILED, 'Transfer Failed'),
            (TRANSFER_BAD_REQUEST, 'Transfer Bad Request'),
            (TRANSFER_SERVER_ERROR, 'Transfer Server Error'),
            )

    # Exception classes
    SiteError = type('SiteError', (Exception,), {})
    TransferError = type('TransferError', (Exception,), {})
    InvalidUIDError = type('InvalidUIDError', (Exception,), {})

    @classmethod
    def find_status(cls, code):
        try:
            return filter(lambda s: s[0] == code, cls.statuses)[0]
        except IndexError:
            return None

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
        status_tuple = TransferService.find_status(code)
        if status_tuple is None:
            return None
        status['status'] = status_tuple[0]
        status['human_status'] = status_tuple[1]
        status['timestamp'] = timestamp
        status['message'] = status.get('message', '')
        #status['progress'] = status.get('progress', '')
        return status

    def push_experiment_to_institutions(self, experiment, owners):
        return self.manager.push_experiment_to_institutions(experiment, owners)


class HttpClient(object):
    STATUS_OK = 200
    def _request(self, url, method, headers, data):
        body = None
        if data:
            body = urllib.urlencode(data)
        default_headers = {'Content-type': 'application/json'}
        if headers:
            default_headers.update(headers)
        h = httplib2.Http()
        h.force_exception_to_status_code = True
        resp, content = h.request(url, method, headers=default_headers, body=body)
        return (resp, content)

    def get(self, url, headers={}, data={}):
        return self._request(url, 'GET', headers, data)

    def post(self, url, headers={}, data={}):
        return self._request(url, 'POST', headers, data)


class TransferClient(object):
    client_class = HttpClient

    def __init__(self):
        self.client = self.client_class()
        self.key = getattr(settings, 'SYNC_CLIENT_KEY', '')

    def request_file_transfer(self, synced_exp):
        from_url = synced_exp.provider_url
        logger.debug('Sending file request to %s' % from_url)
        # This could differ from institution to institution, so a better method
        # of setting the right path is probably needed.
        dest_file_path = str(synced_exp.experiment.id)
        # This reverse assumes that the urlpatterns are the same at each end.
        # It might be better if the from_url pointed directly to the file transfer
        # view, so we don't need to guess.
        # A proper restful discovery service would be a better way to solve this.
        url = from_url + reverse('sync-get-experiment')
        headers = { 'X_MYTARDIS_KEY': self.key }
        data = {}
        data['uid'] = synced_exp.uid
        data['dest_path'] = dest_file_path
        data['site_settings_url'] = settings.MYTARDIS_SITE_URL \
                + reverse('tardis-site-settings')
        resp, content = self.client.post(url, headers=headers, data=data)
        if resp.status != self.client_class.STATUS_OK:
            logger.error('File transfer request to %s failed: %s' % (url, resp.reason))
            return False

        return resp.status == self.client_class.STATUS_OK

    def get_status(self, synced_exp):
        url = synced_exp.provider_url \
                + reverse('sync-transfer-status', args=[synced_exp.uid])
        headers = { 'X_MYTARDIS_KEY': self.key }
        resp, content = self.client.get(url, headers=headers)
        dict_from_json = self._handle_status_result(resp, content)
        synced_exp.save_status(dict_from_json)
        return dict_from_json

    def _handle_status_result(self, resp, content):
        if resp.status == self.client_class.STATUS_OK:
            try:
                return json.loads(content)
            except ValueError:
                error = 'Invalid JSON: %s' % content
        else:
            error = 'HTTP error %s: %s' % (resp.status, resp.reason)
        logger.warning('Status request to %s failed: %s' % (resp['content-location'], error))
        return {
            'status': TransferService.TRANSFER_SERVER_ERROR,
            'message': error,
            }

