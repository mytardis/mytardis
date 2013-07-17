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
from optparse import make_option
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.log import dictConfig

from tardis.tardis_portal.models import Location, Experiment
from tardis.tardis_portal.transfer import TransferError

from tardis.apps.migration import ArchivingError, create_experiment_archive, \
    save_archive_record, remove_experiment, remove_experiment_data, \
    last_experiment_change
from tardis.apps.migration.models import Archive

from tardis.tardis_portal.logging_middleware import LOGGING, LoggingMiddleware

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    LoggingMiddleware()
    args = 'archive_experiment <id> ...'
    help = 'This command archives MyTardis Experiments\n'

    option_list = BaseCommand.option_list + (
        make_option('-a', '--all',
                    action='store_true',
                    dest='all',
                    help='Process all datafiles'), 
        make_option('-l', '--location',
                    action='store',
                    dest='location',
                    help='The location for sending the archive. ' \
                        'The default location is %s' % \
                        settings.DEFAULT_ARCHIVE_LOCATION), 
        make_option('-d', '--directory',
                    action='store',
                    dest='directory',
                    help='A (local) directory for storing the archives'),
        make_option('-n', '--dryRun',
                    action='store_true',
                    dest='dryRun',
                    default=False,
                    help='Dry-run mode just lists the experiments that' \
                        ' would be archived'), 
        make_option('-i', '--incremental',
                    action='store_true',
                    dest='incremental',
                    default=False,
                    help='Incremental mode just archives experiments that' \
                        ' are new or have changed since their last archive'), 
        make_option('--removeData',
                    action='store_true',
                    dest='removeData',
                    default=False,
                    help="Remove the experiment's online data files after" \
                        " it has been archived.  The Experiment, Dataset" \
                        " and Datafile records remain online, together with" \
                        " any properties and access control information."), 
        make_option('--removeAll',
                    action='store_true',
                    dest='removeAll',
                    default=False,
                    help='Remove the experiment entirely after' \
                        ' it has been archived.  This removes all traces' \
                        ' of the experiment and dependent datasets and' \
                        ' datafiles.  All that will remain online are the' \
                        ' archive records.'),
        make_option('--minSize',
                    action='store',
                    dest='minSize',
                    default=None,
                    help='The minimum allowed archive size'),
        make_option('--maxSize',
                    action='store',
                    dest='maxSize',
                    default=None,
                    help='The maximum allowed archive size'),
        make_option('--maxTotalSize',
                    action='store',
                    dest='maxTotalSize',
                    default=None,
                    help='The aggregate archive size limit'),
        )
    
    conf = dictConfig(LOGGING)
    
    def handle(self, *args, **options):
        # Option processing
        self.verbosity = int(options.get('verbosity', 1))
        self.remove_all = options.get('removeAll', False)
        self.remove_data = options.get('remove', False)
        self.dryRun = options.get('dryRun', False)
        self.incremental = options.get('incremental', False)
        self.location = self._get_destination(
            options.get('location', None),
            settings.DEFAULT_ARCHIVE_LOCATION)
        self.directory = options.get('directory', None)
        self.all = options.get('all', False)
        self.maxSize = self._size_opt(options, 'maxSize', 
                                      'DEFAULT_ARCHIVE_MAX_SIZE')
        self.minSize = self._size_opt(options, 'minSize', 
                                      'DEFAULT_ARCHIVE_MIN_SIZE')
        self.maxTotalSize = self._size_opt(options, 'maxTotalSize', 
                                           'DEFAULT_ARCHIVE_MAX_TOTAL, SIZE')

        # Ping test
        if not (self.directory or self.dryRun or 
                self._ping(self.location, 'Archive')):
            return
        
        # Process the experiments to be archived
        self.transfer_count = 0
        self.error_count = 0
        self.total_size = long(0)
        if self.all:
            self._all_experiments()
        else:
            self._experiments(args)
        self._stats()

    def _size_opt(self, options, key, dflt_key):
        value = options.get(key, None)
        if not value:
            if self.location:
                value = getattr(self.location.provider, key, None)
                if not value:
                    value = getattr(settings, dflt_key, None)
        if value:
            return long(value)
        else:
            return None
            
    def _stats(self):
        if not self.dryRun and self.verbosity > 0:
            self.stdout.write("Archived %s experiments with %s errors\n" %
                              (self.transfer_count, self.error_count))
            if self.verbosity > 1:
                self.stdout.write("Total archive size %s bytes\n" % 
                                  self.total_size)
            
    def _all_experiments(self):
        for exp in Experiment.objects.all():
            self._process_experiment(exp)
            if self.maxTotalSize and self.total_size >= self.maxTotalSize:
                return
            
    def _experiments(self, args):
        for id in args:
            try:
                self._process_experiment(Experiment.objects.get(id=id))
            except Experiment.DoesNotExist:
                self.stderr.write('Experiment %s does not exist\n' % id) 
            if self.maxTotalSize and self.total_size >= self.maxTotalSize:
                return
               
    def _process_experiment(self, exp):
        experiment_changed = last_experiment_change(exp)
        if self.incremental:
            try:
                last_archive = Archive.objects.filter(experiment=exp) \
                    .order_by('-experiment_changed')[0]
                if last_archive.experiment_changed >= experiment_changed:
                    return
            except IndexError:
                pass
        if self.dryRun:
            self.stdout.write('Would have archived experiment %s\n' % exp.id)
            return
        tmp_file = None
        try:
            if self.directory:
                pathname = os.path.join(self.directory, 
                                        '%s-archive.tar.gz' % exp.id)
                archive = create_experiment_archive(
                    exp, open(pathname, 'wb'), 
                    minSize=self.minSize, maxSize=self.maxSize)
            else:
                tmp_file = NamedTemporaryFile(
                    prefix='mytardis_tmp_ar', suffix='.tar.gz', 
                    delete=False)
                archive = create_experiment_archive(
                    exp, tmp_file, minSize=self.minSize, maxSize=self.maxSize)
                archive.experiment_changed=experiment_changed
                save_archive_record(archive, self.location.provider.base_url)

            self.total_size += archive.size
            if self.maxTotalSize and self.total_size >= self.maxTotalSize:
                raise ArchivingError('Exceeded total size') 

            if self.directory: 
                if self.verbosity > 0:
                    self.stdout.write('Archived experiment %s to %s\n' %
                                      (exp.id, pathname))
            else:
                self.location.provider.put_archive(
                    tmp_file.name, archive.archive_url)
                if self.verbosity > 0:
                    self.stdout.write('Archived experiment %s to %s\n' %
                                      (exp.id, archive.archive_url))
            if archive.nos_errors > 0:
                self.stderr.write(
                    'Archive for experiment %s is missing %s files\n' % \
                        (exp.id, archive.nos_errors))
            self.transfer_count += 1
            if self.remove_all:
                remove_experiment(exp)
            elif self.remove_data:
                remove_experiment_data(exp, archive.archive_url, location)

        except ArchivingError as e:
            logger.info('Archiving error', exc_info=sys.exc_info())
            self.stderr.write(
                'archiving failed for experiment %s : %s\n' % \
                    (exp.id, e.args[0]))
            self.error_count += 1
        except TransferError as e:
            logger.info('Transfer error', exc_info=sys.exc_info())
            self.stderr.write(
                'archive export failed for experiment %s : %s\n' % \
                    (exp.id, e.args[0]))
            self.error_count += 1
        finally:
            if tmp_file:
                os.unlink(tmp_file.name)
                tmp_file.close()

    def _ping(self, location, label):
        if not location.provider.alive():
            self.stderr.write(
                '%s location %s is not responding: giving up\n' % \
                    (label, location.name))
            return False
        else:
            return True

    def _get_destination(self, destName, default):
        if not destName:
            if not default:
                raise CommandError("No default destination configured")
            else:
                destName = default
        dest = Location.get_location(destName)
        if not dest:
            raise CommandError("Destination %s not known" % destName)
        return dest
