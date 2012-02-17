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
from suds.client import Client

from django.conf import settings

from tardis.apps.sync.site_parser import SiteParser
from tardis.apps.sync.site_settings_parser import SiteSettingsParser
from tardis.apps.sync.managers import SyncManagerTransferError, SyncManagerInvalidUIDError
from tardis.tardis_portal.models import Experiment, ExperimentParameter

logger = logging.getLogger('tardis.mecat')

#
# For watching over things on the provider side of the 
# sync operation. Not sure whether most of this could just
# be done in the object manager of the SyncedExperiment model
#

class SyncManager():

    TRANSFER_COMPLETE = 1
    TRANSFER_IN_PROGRESS = 2
    TRANSFER_FAILED = 3

    statuses = (
            (TRANSFER_COMPLETE, 'Transfer Complete'),
            (TRANSFER_IN_PROGRESS, 'Transfer In Progress'),
            (TRANSFER_FAILED, 'Transfer Failed'),
            )

    def __init__(self, institution='tardis'):
        
        self.institution = institution
        url = settings.MYTARDIS_SITES_URL
        logger.debug('fetching mytardis sites from %s' % url)
        try:
            sites_username = settings.MYTARDIS_SITES_USERNAME
            sites_password = settings.MYTARDIS_SITES_PASSWORD
        except AttributeError:
            sites_username = ''
            sites_password = ''

        self.site_parser = SiteParser(url, sites_username, sites_password)


    def generate_exp_uid(self, experiment):
        uid_str = "%s.%s" % (self.institution, experiment.pk)
        return uid_str 
    
    def exp_from_uid(self, uid):
        try: 
            [institution, pk] = uid.split('.')
        except ValueError:
            raise SyncManagerInvalidUIDError()
        
        if institution != self.institution:
            raise SyncManagerInvalidUIDError()
        try:
            exp = Experiment.objects.get(pk=int(pk))
        except Experiment.DoesNotExist:
            raise SyncManagerInvalidUIDError()
        
        return exp

    def get_sites(self):
        #TODO rewrite the parser to get tuples straight up
        # TODO generator function
        sites = []
        try:
            site_names = self.sp.getSiteNames()
        except:
            #TODO
            return
        
        for name in site_names:
            try:
                url = self.sp.getSiteSettingsURL(name)
                username = self.sp.getSiteSettingsUsername(name)
                password = self.sp.getSiteSettingsPassword(name)
            except:
                #TODO
                return

            sites.append((name, url, username, password))

        return sites

    def start_file_transfer(self, exp, site_settings_url, site_username, site_password):
       
        # read remote MyTARDIS configV
        self.ssp = SiteSettingsParser(site_settings_url, site_username, site_password)
       
        # get EPN (needed to kick-off vbl gridftp transfer)
        epn = ExperimentParameter.objects.get(parameterset__experiment=exp,
                                                        name__name='EPN').string_value
        
        client = Client(settings.VBLSTORAGEGATEWAY, cache=None)

        x509 = self.self.ssp.getTransferSetting('password')
        # build destination path
        dirname = os.path.abspath(
            os.path.join(self.ssp.getTransferSetting('serversite'), )
            )
        logger.debug('destination url:  %s' % site_settings_url)
        logger.debug('destination path: %s' % dirname)

        # contact VBL
        key = client.service.VBLstartTransferGridFTP(
            self.ssp.getTransferSetting('user'),
            x509,
            epn,
            '/Frames\\r\\nTARDIS\\r\\n',
            self.ssp.getTransferSetting('sl'),
            dirname,
            self.ssp.getTransferSetting('optionFast'),
            self.ssp.getTransferSetting('optionPenable'),
            self.ssp.getTransferSetting('optionP'),
            self.ssp.getTransferSetting('optionBSenable'),
            self.ssp.getTransferSetting('optionBS'),
            self.ssp.getTransferSetting('optionTCPBenable'),
            self.ssp.getTransferSetting('optionTCPBS'))

        if key.startswith('Error:'):
            logger.error('[vbl] %s: epn %s' % (key, epn))
            raise SyncManagerTransferError()
        else:
            logger.info('[vbl] %s: pn %s' % (key, epn))

    def get_status(self, uid):
        #TODO kiz magic
        return SyncManager.TRANSFER_COMPLETE
