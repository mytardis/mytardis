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
import urllib2
from suds.client import Client

from django.conf import settings

from tardis.apps.sync.site_parser import SiteParser
from tardis.apps.sync.site_settings_parser import SiteSettingsParser
from tardis.apps.sync.managers import SyncManagerTransferError, SyncManagerInvalidUIDError

from tardis.tardis_portal.models import Experiment, ExperimentParameter

# TODO surely this goes in 'forms', if not in our app?
from tardis.tardis_portal import MultiPartForm

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

    # originally '_register_file_settings' in parser
    #
    # TODO change the mecat-as app etc to call this 
    # rather than the parser.py files registration logic
    #
    def push_experiment_to_institutions(self, experiment, owners):
        """
        ingests meta-data and transfers data to experiment owner's
        mytardis instance at the home institute

        :keyword request: Django request
        :keyword cleaned_data: cleaned form data
        :keyword expid: id of experiment to be transfered
        """

        # sites which will receive a copy of the data
        sites = []

        # register at home institute

        # owner list should be generated outside
        #owners = re.compile(r'\s+').split(cleaned_data['experiment_owner'])
        for owner in owners:
        #    if owner == '':
        #       continue

            # get list of site from master tardis instance (Monash)
            # TODO: might be better to store these sites in Django's
            # sites table!
            url = settings.MYTARDIS_SITES_URL
            logger.debug('fetching mytardis sites from %s' % url)
            #try:
            #    sites_username = settings.MYTARDIS_SITES_USERNAME
            #    sites_password = settings.MYTARDIS_SITES_PASSWORD
            #except AttributeError:
            #    # maybe we get the site list from a file...
            #    sites_username = ''
            #    sites_password = ''

            # username and password must be set if another site is contacted
            #sp = SiteParser(url, sites_username, sites_password)
            

            # loop over sites
            for name in self.sp.getSiteNames():
                url = self.sp.getSiteSettingsURL(name)
                # fetch a MyTARDIS site's config
                logger.debug('fetching site config for %s from %s' % (name, url))
                try:
                    ssp = SiteSettingsParser(url,
                                             self.sp.getSiteSettingsUsername(name),
                                             self.sp.getSiteSettingsPassword(name))
                except:
                    logger.exception('fetching site config from %s FAILED' % url)
                    continue

                # is the email domain of the experiment's owner registered
                # by any site?
                siteOwners = []
                for owner in owners:
                    for domain in ssp.getEmailEndswith():
                        if owner.endswith(domain):
                            siteOwners.append(owner)

                # register meta-data and file transfer request at another
                # MyTARDIS instance
                if siteOwners:
                    # Create the form with simple fields
                    uid = self.sm.generate_exp_uid(experiment)
                    mpform = MultiPartForm()
                    mpform.add_field('username', ssp.getRegisterSetting('username'))
                    mpform.add_field('password', ssp.getRegisterSetting('password'))
                    mpform.add_field('from_url', request.build_absolute_uri())
                    mpform.add_field('originid', uid)#str(expid))

                    for siteOwner in siteOwners:
                        mpform.add_field('experiment_owner', siteOwner)

                    protocol = ssp.getRegisterSetting('fileProtocol')

                    # export METS file
                    filename = 'mets_expid_%i_%s' % (experiment.id, protocol)
                    logger.debug('=== extracting mets file for experiment %i ' % uid)
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

                    ws = ssp.getRegisterSetting('url')
                    logger.debug('about to send register request to site %s' % ws)
                    # build the request
                    requestmp = urllib2.Request(ws)
                    requestmp.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
                    body = str(mpform)
                    requestmp.add_header('Content-type', mpform.get_content_type())
                    requestmp.add_header('Content-length', len(body))

                    # logger.debug('OUTGOING DATA: ' + body)
                    logger.debug('SERVER RESPONSE: ' + urllib2.urlopen(requestmp, body, 99999).read())

                    f.close()
                    sites.append(url)

            # return a list of registered sites
            return sites

        return []

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
