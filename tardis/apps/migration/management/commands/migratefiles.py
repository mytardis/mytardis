#
# Copyright (c) 2012, Centre for Microscopy and Microanalysis
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

import sys
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tardis.apps.migration import Destination, MigrationError, \
    MigrationScorer, migrate_datafile_by_id
from tardis.tardis_portal.models import Dataset_File, Dataset, Experiment

class Command(BaseCommand):
    args = '<subcommand> <arg> ...'
    help = 'This command performs migrates files for MyTardis Experiments, ' \
        'Datasets and Datafiles to configured secondary file stores.  Each ' \
        'individual Datafile is migrated atomically, but there are no ' \
        'guarantees of atomicity at the Dataset or Experiment level.  The ' \
        'following subcommands are supported:\n' \
        '    datafile <id> ...     : migrates files for datafiles\n' \
        '    dataset <id> ...      : migrates files for datasets\n' \
        '    experiment <id> ...   : migrates files for experiments\n' \
        '    reclaim <N>           : migrate files to reclaim N bytes\n' \
        '    destinations          : lists the recognized destinations' 
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dest',
                    action='store',
                    dest='dest',
                    default=settings.DEFAULT_MIGRATION_DESTINATION,
                    help='The destination for the transfer. ' \
                        'The default destination is %s' % \
                        settings.DEFAULT_MIGRATION_DESTINATION), 
        make_option('-n', '--dryRun',
                    action='store',
                    dest='dryRun',
                    default=False,
                    help='Dry run mode just lists the datafiles that' \
                        ' would be migrated'), 
        )

    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.dryRun = options.get('dryRun', False)
        if len(args) == 0:
            raise CommandError("Expected a subcommand")
        subcommand = args[0]
        if subcommand == 'destinations':
            self._list_destinations()
            return
        elif subcommand == 'score':
            self._score_all_datafiles()
            return
        args = args[1:]
        self.dest = self._get_destination(options.get('dest', None))
        if not self.dest:
            return
        if subcommand == 'reclaim':
            self._reclaim(args)
        elif subcommand == 'datafile' or subcommand == 'datafiles':
            self._datafiles(args)
        elif subcommand == 'dataset' or subcommand == 'datasets':
            self._datasets(args)
        elif subcommand == 'experiment' or subcommand == 'experiments':
            self._experiments(args)
        else:
            raise CommandError("Unrecognized subcommand: %s" % subcommand)

    def _datafiles(self, args):
        ids = []
        for id in args:
            try:
                Dataset_File.objects.get(id=id)
                ids.append(id)
            except Dataset_File.DoesNotExist:
                self.stderr.write('Datafile %s does not exist\n' % id)
        self._migrate_datafiles(args, ids)

    def _datasets(self, args):
        ids = []
        for id in args:
            ids.extend(self._ids_for_dataset(id))
        self._migrate_datafiles(args, ids)

    def _experiments(self, args):
        ids = []
        for id in args:
            ids.extend(self._ids_for_experiment(id))
        self._migrate_datafiles(args, ids)

    def _migrate_datafiles(self, args, ids):
        if len(args) == 0:
            raise CommandError("Expected one or more ids after the subcommand")
        elif len(ids) == 0:
            raise CommandError("No Datafiles selected")

        for id in ids:
            try:
                if self.dryRun:
                    self.stdout.write('Would have migrated datafile %s\n' % id)
                else:
                    migrate_datafile_by_id(id, self.dest)
                    if self.verbosity > 1:
                        self.stdout.write('Migrated datafile %s\n' % id)
                    
            except Dataset_File.DoesNotExist:
                self.stderr.write('Datafile %s does not exist\n' % id)
            except MigrationError as e:
                self.stderr.write( \
                    'Migration failed for datafile %s : %s\n' % \
                        (id, e.args[0]))
        
    def _ids_for_dataset(self, id):
        try:
            dataset = Dataset.objects.get(id=id)
            return Dataset_File.objects.filter(dataset=id).\
                values_list('id', flat=True)
        except Dataset.DoesNotExist:
            self.stderr.write('Dataset %s does not exist\n' % id)
            return []

    def _ids_for_experiment(self, id):
        try:
            experiment = Experiment.objects.get(id=id)
            return Dataset_File.objects.\
                filter(dataset__experiments__id=id).\
                values_list('id', flat=True)
        except Experiment.DoesNotExist:
            self.stderr.write('Experiment %s does not exist\n' % id)
            return []

    def _get_destination(self, destName):
        if not destName: 
            if not settings.DEFAULT_MIGRATION_DESTINATION:
                raise CommandError("No default destination has been configured")
            destName = settings.DEFAULT_MIGRATION_DESTINATION
        try:
            return Destination(destName)
        except MigrationError as e:
            raise CommandError("Migration error: %s" % e.args[0])
        except ValueError:
            raise CommandError("Destination %s not known" % destName)

    def _list_destinations(self):
        for dest in settings.MIGRATION_DESTINATIONS:
            self.stdout.write(dest['name'])

    def _score_all_datafiles(self):
        scores = MigrationScorer().score_all_datafiles()
        total = 0
        for entry in scores:
            datafile = entry[0]
            try:
                total += int(datafile.size)
            except:
                pass
            self.stdout.write("datafile %s / %s, size = %s, " \
                              "score = %s, total_size = %d" % \
                                  (datafile.url, datafile.id, 
                                   datafile.size, entry[1], total)) 
            
    def _reclaim(self, args):
        if len(args) != 1:
            raise CommandError("reclaim subcommand requires an argument")
        try:
            required_amount = int(args[0])
        except:
            raise CommandError("reclaim argument must be an integer")
        scores = MigrationScorer().score_all_datafiles()
        total = 0
        for entry in scores:
            if total >= required_amount:
                break
            datafile = entry[0]
            if self.verbosity > 1:
                if self.dryRun:
                    self.stdout.write("would have migrated %s / %s " \
                                          "saving %d bytes" % \
                                          (datafile.url, datafile.id, 
                                           datafile.size))
                else:
                    self.stdout.write("migrating %s / %s saving %d bytes" % \
                                          (datafile.url, datafile.id, 
                                           datafile.size))
            total += int(datafile.size) 
            if not self.dryRun:
                migrate_datafile(datafile, self.dest)
        if self.dryRun:
            self.stdout.write("Would have reclaimed %d bytes" % total)
        else:
            self.stdout.write("Reclaimed %d bytes" % total)
