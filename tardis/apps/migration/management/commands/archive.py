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
    args = 'archive <id> ...'
    help = 'This command archives MyTardis Experiments\n'

    option_list = BaseCommand.option_list + (
        make_option('-a', '--all',
                    action='store_true',
                    dest='all',
                    help='Process all experiments'), 
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
        make_option('-o', '--sendOffline',
                    action='store_true',
                    dest='sendOffline',
                    default=False,
                    help='Causes archives to be pushed offline at the' \
                        ' archive location after verification'), 
        make_option('-c', '--checksums',
                    action='store_true',
                    dest='checksums',
                    default=False,
                    help='Forces verification of archive checksums after' \
                        ' file transfer. (This is implied by --removeAll' \
                        ' or --removeData.)'), 
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
        make_option('--keepOnly',
                    action='store',
                    dest='keepOnly',
                    default=None,
                    help='The number of archives to keep'),
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
        make_option('-f', '--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    help='Turn the minSize and maxSize options into warnings'),
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
        self.sendOffline = options.get('sendOffline', False)
        self.all = options.get('all', False)
        self.force = options.get('force', False)
        self.keepOnly = self._int_opt(options, 'keepOnly', '',
                                      scale_allowed=False)
        self.checksums = options.get('checksums', False)
        if self.keepOnly != None and self.keepOnly <= 0:
            raise CommandError('--keepOnly value must be > zero')
        self.maxSize = self._int_opt(options, 'maxSize', 
                                     'DEFAULT_ARCHIVE_MAX_SIZE')
        self.minSize = self._int_opt(options, 'minSize', 
                                     'DEFAULT_ARCHIVE_MIN_SIZE')
        self.maxTotalSize = self._int_opt(options, 'maxTotalSize', 
                                          'DEFAULT_ARCHIVE_MAX_TOTAL, SIZE')
        self.paranoid = self.remove_all or self.remove_data or self.checksums

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

    def _check_size(self, archive):
        if self.minSize and archive.size < self.minSize:
            if self.force:
                self.stderr.write('Warning: archive for experiment %s '
                                  'is too small\n' % archive.experiment.id)
                return False
            else:
                raise ArchivingError('Archive for experiment %s is too small' %
                                     archive.experiment.id)
        if self.maxSize and archive.size > self.maxSize:
            if self.force:
                self.stderr.write('Warning: archive for experiment %s '
                                  'is too big\n' % archive.experiment.id)
                return False
            else:
                raise ArchivingError('Archive for experiment %s is too big' %
                                     archive.experiment.id)

        self.total_size += archive.size
        if self.maxTotalSize and self.total_size >= self.maxTotalSize:
            raise ArchivingError('Exceeded total size') 
        return True

    def _int_opt(self, options, key, dflt_key, scale_allowed=True):
        value = options.get(key, None)
        if not value:
            if self.location:
                value = getattr(self.location.provider, key, None)
                if not value:
                    value = getattr(settings, dflt_key, None)
        if value:
            if scale_allowed:
                try:
                    return parse_scaled_number(value)
                except ValueError:
                    raise CommandError(
                        "--%s argument (%s) must be a non-negative" \
                            " number followed by an optional scale" \
                            " factor (K, M, G or T)" % (key, value))
            else:
                try:
                    return long(value)
                except ValueError:
                    raise CommandError(
                        "--%s argument (%s) must be an integer" % (key, value))
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
        maxSize = None if self.force else self.maxSize 
        try:
            if self.directory:
                pathname = os.path.join(self.directory, 
                                        '%s-archive.tar.gz' % exp.id)
                archive = create_experiment_archive(
                    exp, open(pathname, 'wb'), maxSize=maxSize)
            else:
                tmp_file = NamedTemporaryFile(
                    dir=settings.ARCHIVE_TEMP_DIR,
                    prefix='mytardis_tmp_ar', suffix='.tar.gz', 
                    delete=False)
                archive = create_experiment_archive(
                    exp, tmp_file, maxSize=maxSize)

            size_ok = self._check_size(archive)

            if self.directory: 
                if self.verbosity > 0:
                    self.stdout.write('Archived experiment %s to %s\n' %
                                      (exp.id, pathname))
            else:
                try:
                    provider = self.location.provider
                    archive.experiment_changed=experiment_changed
                    (md5sum, sha512sum, length, _) = \
                        generate_file_checksums(open(tmp_file.name))
                    archive.sha512sum = sha512sum
                    save_archive_record(archive, provider.base_url)
                    provider.put_archive(tmp_file.name, archive.archive_url)
                    provider.check_transfer(archive.archive_url,
                                            {'length': str(length),
                                             'md5sum': md5sum,
                                             'sha512sum': sha512sum},
                                            require_checksum=self.paranoid)
                    if self.sendOffline and size_ok:
                        try:
                            provider.take_offline(archive.archive_url)
                        except NotImplementedError:
                            self.stderr.write(
                                'Archive location does not ' 
                                'support --sendOffline ... ignoring it')
                            self.sendOffline = False
                    if self.verbosity > 0:
                        self.stdout.write('Archived experiment %s to %s\n' %
                                          (exp.id, archive.archive_url))
                except Exception as e:
                    if archive.id:
                        archive.delete()
                    raise e
            if archive.nos_errors > 0:
                self.stderr.write(
                    'Archive for experiment %s is missing %s of %s files\n' % \
                        (exp.id, archive.nos_errors, 
                         archive.nos_errors + archive.nos_files))
            self.transfer_count += 1
            if self.remove_all:
                remove_experiment(exp)
            elif self.remove_data:
                remove_experiment_data(exp, archive.archive_url, location)

            if self.keepOnly:
                self._prune_archives(exp)

        except ArchivingError as e:
            logger.info('Archiving error', exc_info=sys.exc_info())
            self.stderr.write(
                'Archiving failed for experiment %s : %s\n' % \
                    (exp.id, e.args[0]))
            self.error_count += 1
        except TransferError as e:
            logger.info('Transfer error', exc_info=sys.exc_info())
            self.stderr.write(
                'Archive export failed for experiment %s : %s\n' % \
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

    def _prune_archives(self, exp):
        archives = Archive.objects.filter(experiment=exp) \
            .order_by('archive_created')
        count = len(archives)
        for i in range(0, count - self.keepOnly):
            archive = archives[i]
            url = archive.archive_url
            location = Location.get_location_for_url(url)
            if location:
                try:
                    location.provider.remove_file(url)
                except TransferError:
                    logger.info('Failed to delete archive %s' % url, 
                                exc_info=sys.exc_info())
                archive.delete()
            
            
            
