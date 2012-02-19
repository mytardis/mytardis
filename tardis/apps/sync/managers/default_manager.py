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
import datetime

from django.conf import settings

from tardis.apps.sync.site_parser import SiteParser
from tardis.apps.sync.site_settings_parser import SiteSettingsParser
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal import MultiPartForm

from ..transfer_service import TransferService

logger = logging.getLogger('tardis.mecat')

#
# For watching over things on the provider side of the 
# sync operation. Not sure whether most of this could just
# be done in the object manager of the SyncedExperiment model
#

class SyncManager(object):

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


    def _exp_from_uid(self, uid):
        try:
            [institution, pk] = uid.split('.')
        except ValueError:
            raise TransferService.InvalidUIDError()

        if institution != self.institution:
            raise TransferService.InvalidUIDError()
        try:
            exp = Experiment.objects.get(pk=int(pk))
        except Experiment.DoesNotExist:
            raise TransferService.InvalidUIDError()

        return exp


    def _get_sites(self):
        #TODO rewrite the parser to get tuples straight up
        # TODO generator function
        sites = []
        try:
            site_names = self.site_parser.getSiteNames()
        except:
            return TransferService.SiteError('Error parsing site settings')

        for name in site_names:
            try:
                url = self.site_parser.getSiteSettingsURL(name)
                username = self.site_parser.getSiteSettingsUsername(name)
                password = self.site_parser.getSiteSettingsPassword(name)
            except:
                return TransferService.SiteError('Error parsing site settings')

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
            logger.debug('fetching mytardis sites from %s' % url)

            # loop over sites
            for (name, url, u, p) in self._get_sites():
                # fetch a MyTARDIS site's config
                logger.debug('fetching site config for %s from %s' % (name, url))
                try:
                    ssp = self.get_site_settings(url)
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
                    uid = self.generate_exp_uid(experiment)
                    mpform = MultiPartForm()
                    mpform.add_field('username', ssp.getRegisterSetting('username'))
                    mpform.add_field('password', ssp.getRegisterSetting('password'))
                    mpform.add_field('from_url', request.build_absolute_uri())
                    mpform.add_field('originid', uid)

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

                    # This should be made into a background task.
                    # logger.debug('OUTGOING DATA: ' + body)
                    logger.debug('SERVER RESPONSE: ' + urllib2.urlopen(requestmp, body, 99999).read())

                    f.close()
                    sites.append(url)

            # return a list of registered sites
            return sites

        return []


    def _get_site_settings(self, site_settings_url):
        # check if the requesting site is known (very basic
        # security)
        for name, url, u, p in self._get_sites():
            if site_settings_url == url:
                # read remote MyTARDIS config
                logger.info('Found site "%s", retrieving settings.' % name)
                return SiteSettingsParser(site_settings_url, u, p)
        raise TransferService.SiteError('Unknown site')


    def start_file_transfer(self, uid, site_settings_url, dest_path):
        exp = self._exp_from_uid(uid)
        site_settings = self._get_site_settings(site_settings_url)
        return self._start_file_transfer(exp, site_settings, dest_path)


    def get_status(self, uid):
        exp = self._exp_from_uid(uid)
        return self._get_status(exp)


    def _start_file_transfer(self, experiment, settings, path):
        return True


    def _get_status(self, experiment):
        return (TransferService.TRANSFER_IN_PROGRESS, datetime.now(), {})

