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

import sys, re, os.path
from optparse import make_option
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.log import dictConfig

from tardis.tardis_portal.models import Location, Experiment
from tardis.tardis_portal.transfer import TransferError

from tardis.apps.migration import ArchivingError, create_experiment_archive, \
    create_archive_record, remove_experiment, remove_experiment_data, \
    last_experiment_change
from tardis.apps.migration.models import Archive

from tardis.tardis_portal.logging_middleware import LOGGING

class Command(BaseCommand):
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
                        ' archive records.') 
        )
    
    conf = dictConfig(LOGGING)
    
    def handle(self, *args, **options):
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
        if not (self.directory or self.dryRun or 
                self._ping(self.location, 'Archive')):
            return
        self.transfer_count = 0
        self.error_count = 0
        if self.all:
            self._all_experiments()
        else:
            self._experiments(args)
        self._stats()

    def _stats(self):
        if not self.dryRun and self.verbosity > 0:
            self.stdout.write("Archived %s experiments with %s errors\n" %
                              (self.transfer_count, self.error_count))
            
    def _all_experiments(self):
        for exp in Experiment.objects.all():
            self._process_experiment(exp)
            
    def _experiments(self, args):
        for id in args:
            try:
                self._process_experiment(Experiment.objects.get(id=id))
            except Experiment.DoesNotExist:
                print "Not exist\n"
                self.stderr.write('Experiment %s does not exist\n' % id)
                
    def _process_experiment(self, exp):
        experiment_changed = last_experiment_change(exp)
        print 'experiment_changed is %s\n' % experiment_changed
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
                create_experiment_archive(exp, open(pathname, 'wb'))
            else:
                tmp_file = NamedTemporaryFile(prefix='mytardis_tmp_ar',
                                              suffix='.tar.gz',
                                              delete=False)
                create_experiment_archive(exp, tmp_file)
            if not self.directory:
                archive_url = self.location.provider.put_archive(
                    tmp_file.name, exp)
                create_archive_record(exp, archive_url, experiment_changed)
                if self.verbosity > 0:
                    self.stdout.write('Archived experiment %s to %s\n' %
                                      (exp.id, archive_url))
            else:
                archive_url = None
                if self.verbosity > 0:
                    self.stdout.write('Archived experiment %s to %s\n' %
                                      (exp.id, pathname))
                    
            self.transfer_count += 1
            if self.remove_all:
                remove_experiment(exp)
            elif self.remove_data:
                remove_experiment_data(exp, archive_url, location)

        except ArchivingError as e:          
            self.stderr.write(
                'archiving failed for experiment %s : %s\n' % \
                    (exp.id, e.args[0]))
            self.error_count += 1
        except TransferError as e:
            self.stderr.write(
                'archive export failed experiment %s : %s\n' % \
                    (exp.id, e.args[0]))
            self.error_count += 1
        finally:
            if tmp_file:
                os.unlink(tmp_file.name)
        
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
