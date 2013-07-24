#
# Copyright (c) 2013, Centre for Microscopy and Microanalysis
#   (University of Queensland, Australia)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the University of Queensland nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
#

"""
Management command to migrate datafiles, datasets and experiments
"""

import sys, re, os.path, traceback
from datetime import date, timedelta, datetime
from optparse import make_option
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.log import dictConfig

from tardis.tardis_portal.models import Location, Experiment
from tardis.tardis_portal.transfer import TransferError
from tardis.tardis_portal.util import generate_file_checksums, \
    parse_scaled_number

from tardis.apps.migration import ArchivingError, create_experiment_archive, \
    save_archive_record, remove_experiment, remove_experiment_data, \
    last_experiment_change
from tardis.apps.migration.models import Archive

from tardis.tardis_portal.logging_middleware import LOGGING, LoggingMiddleware

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    LoggingMiddleware()
    args = 'listarchives [<id> ...]'
    help = 'This command lists MyTardis experiment archives\n'

    option_list = BaseCommand.option_list + (
        make_option('-a', '--showAll',
                    action='store_true',
                    dest='all',
                    help='List all archives selected rather than just the'
                    ' last for each experiment.'), 
        make_option('-f', '--showFirst',
                    action='store_true',
                    dest='first',
                    help='List first rather than the last archive ' \
                        'last for each experiment.'), 
        make_option('-c', '--count',
                    action='store_true',
                    dest='count',
                    help='Count rather than list archives'), 
        make_option('-e', '--experimentDate',
                    action='store_true',
                    dest='experimentDate',
                    help='Select using experiment_changed date rather than ' \
                        'archive_created date, and show that date'), 
        make_option('-u', '--user',
                    action='store',
                    dest='user',
                    default=None,
                    help='Select archives for this user'),
        make_option('-t', '--title',
                    action='store',
                    dest='title',
                    default=None,
                    help='Select archives with this title'),
        make_option('-d', '--date',
                    action='store',
                    dest='date',
                    default=None,
                    help='Select archives created on this date'),
        make_option('-F', '--fromDate',
                    action='store',
                    dest='fromDate',
                    default=None,
                    help='Select archives created on or after this date'),
        make_option('-T', '--toDate',
                    action='store',
                    dest='toDate',
                    default=None,
                    help='Select archives created on or before this date')
        )
    
    conf = dictConfig(LOGGING)
    
    def handle(self, *args, **options):
        # Option processing
        self.verbosity = int(options.get('verbosity', 1))
        self.all = options.get('all', False)
        self.first = options.get('first', False)
        self.count = options.get('count', False)
        self.user = options.get('user', None)
        self.title = options.get('title', None)
        self.experimentDate = options.get('experimentDate', False)
        self.fromDate = self._get_datetime(options, 'fromDate')
        self.toDate = self._get_datetime(options, 'toDate', end=True)
        if options.get('date', None):
            if self.fromDate or self.toDate: 
                raise CommandError('--date cannot be used with --fromDate '
                                   'or --toDate')
            self.fromDate = self._get_datetime(options, 'date')
            self.toDate = self._get_datetime(options, 'date', end=True)
        elif self.fromDate and self.toDate and self.fromDate > self.toDate:
            raise CommandError('--fromDate must be before --toDate')

        qm = Archive.objects
        if self.user:
            qm = qm.filter(experiment_owner=self.user)
        if self.title:
            qm = qm.filter(experiment_title=self.title)
        if self.fromDate:
            if self.experimentDate:
                qm = qm.filter(experiment_changed__gte=self.fromDate)
            else:
                qm = qm.filter(archive_created__gte=self.fromDate)
        if self.toDate:
            if self.experimentDate:
                qm = qm.filter(experiment_changed__lte=self.toDate)
            else:
                qm = qm.filter(archive_created__lte=self.toDate)

        if len(args) > 0:
            qm = qm.filter(experiment__id__in=map(args, long))

        count = 0
        if self.count and self.all:
            count = qm.count()
        else:
            if self.first:
                qm = qm.order_by('experiment__id', 'archive_created')
            else:
                qm = qm.order_by('experiment__id', '-archive_created')
            prev = None
            for archive in qm.all():
                if not self.all and prev:
                    if prev.experiment == archive.experiment:
                        continue
                if self.count:
                    count += 1
                else:
                    self._print_archive(archive)
                    prev = archive
                    
        if self.count:
            self.stdout.write("There are %s archives meeting the " 
                              "selection criteria\n" % count)

    def _print_archive(self, archive):
        date = archive.experiment_changed if self.experimentDate \
            else archive.archive_created 
        self.stdout.write('%s : %s : %s : %s\n' %
                          (archive.experiment.id,
                           archive.experiment_owner,
                           date,
                           archive.archive_url))
        
        
    def _get_datetime(self, options, key, end=False):
        value = options.get(key, None)
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            pass
        try:
            d = datetime.strptime(value, '%Y-%m-%d')
            if end:
                return d + timedelta(days=1, milliseconds=-1)
            else:
                return d
        except ValueError:
            raise CommandError('"%s" is not recognizable as a (local) ISO 8601 '
                               'datetime or date' % value)
            
            
