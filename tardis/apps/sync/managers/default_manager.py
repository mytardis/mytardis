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
default_manager.py

.. moduleauthor:: Kieran Spear <kispear@gmail.com>
.. moduleauthor:: Shaun O'Keefe <shaun.okeefe.0@gmail.com>

"""
import logging
import os.path
import time
from httplib2 import Http

from django.conf import settings

from tardis.apps.sync.site_manager import SiteManager
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.MultiPartForm import MultiPartForm

from ..transfer_service import TransferService

import logging
logger = logging.getLogger('tardis.mecat')

#
# For watching over things on the provider side of the 
# sync operation. Not sure whether most of this could just
# be done in the object manager of the SyncedExperiment model
#

class SyncManager(object):

    def __init__(self, institution='tardis'):
        self.institution = institution
        self.sites = None
        self.site_manager = SiteManager()

    def generate_exp_uid(self, experiment):
        uid_str = "%s.%s" % (self.institution, experiment.pk)
        return uid_str

    def _exp_from_uid(self, uid):
        try:
            [institution, pk] = uid.split('.')
            pk = int(pk)
        except ValueError:
            raise TransferService.InvalidUIDError('Invalid format')

        if institution != self.institution:
            raise TransferService.InvalidUIDError('Invalid institution')
        try:
            exp = Experiment.objects.get(pk=pk)
        except Experiment.DoesNotExist:
            raise TransferService.InvalidUIDError('Experiment does not exist')
        return exp

    # originally '_register_file_settings' in parser
    #
    # TODO change the mecat-as app etc to call this 
    # rather than the parser.py files registration logic
    #
    def push_experiment_to_institutions(self, experiment, owners):
   
        """
        Transfers experiment metadata to experiment owner's
        MyTardis instance at the home institute.

        :keyword experiment: Experiment object to transfer.
        :keyword owners: Emails of owners of the experiment.
        """
        sites = []
        # loop over sites
        for ss in self.site_manager.sites():
            # is the email domain of the experiment's owner registered
            # by any site?
            site_owners = []
            for owner in owners:
                for domain in ss['email-endswith']:
                    if owner.endswith(domain):
                        site_owners.append(owner)
                        break

            register_settings = ss['register']

            # register meta-data and file transfer request at another
            # MyTARDIS instance
            if site_owners:
                success = self._post_experiment(experiment, site_owners, register_settings)
                sites.append((ss['register']['url'], success))
        # return a list of registered sites
        return sites

    def _post_experiment(self, experiment, site_owners, site_settings):
        uid = self.generate_exp_uid(experiment)
        url = site_settings['url']
        username = site_settings['username']
        password = site_settings['password']
        protocol = site_settings['fileProtocol']

        # Create the form with simple fields
        mpform = MultiPartForm()
        mpform.add_field('username', username)
        mpform.add_field('password', password)
        mpform.add_field('from_url', settings.MYTARDIS_SITE_URL)
        mpform.add_field('originid', uid)

        for owner in site_owners:
            mpform.add_field('experiment_owner', owner)

        # export METS file
        filename = 'mets_expid_%i_%s' % (experiment.id, protocol)
        logger.debug('=== extracting mets file for experiment %s ' % uid)
        from tardis.tardis_portal.metsexporter import MetsExporter
        exporter = MetsExporter()
        if protocol:
            # translate vbl:// into tardis:// url for datafiles
            metsfile = exporter.export(experimentId=experiment.id,
                                       replace_protocols={'vbl': protocol},
                                       filename=filename,
                                       export_images=False)
        else:
            metsfile = exporter.export(experimentId=experiment.id,
                                       filename=filename,
                                       export_images=False)
        logger.debug('=== extraction done, filename = %s' % metsfile)

        f = open(metsfile, "r")
        mpform.add_file('xmldata', 'METS.xml', fileHandle=f)
        body = str(mpform)

        logger.debug('about to send register request to site %s' % url)

        # build the request
        headers = {
            'User-agent': 'MyTardis',
            'Content-type': mpform.get_content_type(),
        }

        # This should be made into a background task.
        # Or rather- the processing on the other end should be.
        h = Http(timeout=9999, disable_ssl_certificate_validation=True)
        h.force_exception_to_status_code = True
        resp, content = h.request(url, 'POST', headers=headers, body=body)
        f.close()

        if resp.status != 200:
            logger.error('Posting experiment to %s failed:' % url)
            logger.error('%s: %s' % (resp.status, resp.reason))
            logger.debug('SERVER RESPONSE: ' + content)
            return False
        return True

    def start_file_transfer(self, uid, site_settings_url, dest_path):
        exp = self._exp_from_uid(uid)
        site_settings = self.site_manager.get_site_settings(site_settings_url)
        if site_settings is None:
            raise TransferService.SiteError('Error retrieving settings for site %s' % site_settings_url)
        return self._start_file_transfer(exp, site_settings['transfer'], dest_path)

    def get_status(self, uid):
        exp = self._exp_from_uid(uid)
        return self._get_status(exp)


    def _start_file_transfer(self, experiment, settings, path):
        return True


    def _get_status(self, experiment):
        return (TransferService.TRANSFER_FAILED, time.time(), {})

