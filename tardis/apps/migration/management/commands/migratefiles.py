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
from django.utils.log import dictConfig

from tardis.apps.migration import Destination, MigrationError, \
    MigrationScorer, migrate_datafile, migrate_datafile_by_id, \
    restore_datafile_by_id
from tardis.tardis_portal.logging_middleware import LOGGING

class Command(BaseCommand):
    args = '<subcommand> <arg> ...'
    help = 'This command performs migrates files for MyTardis Experiments, ' \
        'Datasets and Datafiles to configured secondary file stores.  Each ' \
        'individual Datafile is migrated atomically, but there are no ' \
        'guarantees of atomicity at the Dataset or Experiment level.  The ' \
        'following subcommands are supported:\n' \
        '    migrate [<target> <id> ...] : migrates <target> files to destination \n' \
        '    restore [<target> <id> ...] : restores <target> files from any destination\n' \
        '    mirror [<target> <id> ...]  : copies <target> files to destination\n' \
        '                                  but keeps them local\n' \
        '    reclaim <N>                 : migrate files to reclaim N bytes\n' \
        '    score                       : score and list all files\n' \
        '    destinations                : lists the recognized destinations\n' \
        'where <target> is "datafile", "dataset" or "experiment", and the ' \
        '<id>s are the mytardis numeric ids for the respective objects\n' 

    option_list = BaseCommand.option_list + (
        make_option('-a', '--all',
                    action='store',
                    dest='all',
                    help='Process all datafiles'), 
        make_option('-d', '--dest',
                    action='store',
                    dest='dest',
                    help='The destination for the transfer. ' \
                        'The default destination is %s' % \
                        settings.DEFAULT_MIGRATION_DESTINATION), 
        make_option('-n', '--dryRun',
                    action='store',
                    dest='dryRun',
                    default=False,
                    help='Dry run mode just lists the datafiles that' \
                        ' would be migrated / restored'), 
        make_option('--noRemove',
                    action='store',
                    dest='noRemove',
                    default=False,
                    help='No remove mode migrates / restores without' \
                        ' removing the local / remote copy of the file') 
        )

    conf = dictConfig(LOGGING)

    def handle(self, *args, **options):
        from tardis.tardis_portal.models import \
            Dataset_File, Dataset, Experiment

        self.verbosity = options.get('verbosity', 1)
        self.noRemove = options.get('noRemove', False)
        self.dryRun = options.get('dryRun', False)
        all = options.get('all', False)
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
        self._set_destination(options.get('dest', None))
        if not self.dest:
            return
        if subcommand == 'reclaim':
            self._reclaim(args)
        elif subcommand == 'migrate' or subcommand == 'restore' or \
                subcommand == 'mirror' :
            if subcommand == 'restore' and options['dest']:
                raise CommandError("The --dest option cannot be used with "
                                   "the restore subcommand")
            if all:
                if len(args) != 0:
                    raise CommandError("No target/ids allowed with --all")
            else:
                if len(args) == 0:
                    raise CommandError("Expected a %s target" % subcommand) 
                target = args[0]
                args = args[1:]
            if all:
                self._all_datafiles(subcommand)
            elif target == 'datafile' or target == 'datafiles':
                self._datafiles(args, subcommand)
            elif target == 'dataset' or target == 'datasets':
                self._datasets(args, subcommand)
            elif target == 'experiment' or target == 'experiments':
                self._experiments(args, subcommand)
            else:
                raise CommandError("Unknown target: %s" % target)
        else:
            raise CommandError("Unrecognized subcommand: %s" % subcommand)

    def _all_datafiles(self, subcommand):
        from tardis.tardis_portal.models import Dataset_File
        for id in Dataset_File.objects.all().values_list('id', flat=True):
            self._process_datafile(self, id)

    def _datafiles(self, args, subcommand):
        from tardis.tardis_portal.models import Dataset_File
        ids = []
        for id in args:
            try:
                Dataset_File.objects.get(id=id)
                ids.append(id)
            except Dataset_File.DoesNotExist:
                self.stderr.write('Datafile %s does not exist\n' % id)
        self._process_selected_datafiles(args, ids, subcommand)

    def _datasets(self, args, subcommand):
        ids = []
        for id in args:
            ids.extend(self._ids_for_dataset(id))
        self._process_selected_datafiles(args, ids, subcommand)

    def _experiments(self, args, subcommand):
        ids = []
        for id in args:
            ids.extend(self._ids_for_experiment(id))
        self._process_selected_datafiles(args, ids, subcommand)

    def _process_selected_datafiles(self, args, ids, subcommand):
        if len(args) == 0:
            raise CommandError("Expected one or more ids")
        elif len(ids) == 0:
            raise CommandError("No Datafiles selected")

        for id in ids:
            self._process_datafile(id, subcommand)

    def _process_datafile(self, id, subcommand):
        from tardis.tardis_portal.models import Dataset_File
        if self.dryRun:
            self.stdout.write( \
                'Would have %s datafile %s\n' % \
                    (self._verb(subcommand).lower(), id))
            return
        try:
            if subcommand == 'migrate':
                ok = migrate_datafile_by_id(id, self.dest,
                                            noRemove=self.noRemove)
            elif subcommand == 'mirror':
                ok = migrate_datafile_by_id(id, self.dest, noUpdate=True)
            elif subcommand == 'restore':
                ok = restore_datafile_by_id(id, noRemove=self.noRemove)
            if ok and self.verbosity > 1:
                self.stdout.write('%s datafile %s\n' % \
                                      (self._verb(subcommand), id))
        except Dataset_File.DoesNotExist:
            self.stderr.write('Datafile %s does not exist\n' % id)
        except MigrationError as e:              
            self.stderr.write(
                '%s failed for datafile %s : %s\n' % \
                    (self._noun(subcommand), id, e.args[0]))

    def _verb(self, subcommand):
        if (subcommand == 'migrate'):
            return 'Migrated'
        elif (subcommand == 'restore'):
            return 'Restored'
        elif (subcommand == 'mirror'):
            return 'Mirrored'
        
    def _noun(self, subcommand):
        if (subcommand == 'migrate'):
            return 'Migration'
        elif (subcommand == 'restore'):
            return 'Restoration'
        elif (subcommand == 'mirror'):
            return 'Mirroring'
        
    def _ids_for_dataset(self, id):
        from tardis.tardis_portal.models import Dataset, Dataset_File
        try:
            dataset = Dataset.objects.get(id=id)
            return Dataset_File.objects.filter(dataset=id).\
                values_list('id', flat=True)
        except Dataset.DoesNotExist:
            self.stderr.write('Dataset %s does not exist\n' % id)
            return []

    def _ids_for_experiment(self, id):
        from tardis.tardis_portal.models import Dataset_File, Experiment
        try:
            experiment = Experiment.objects.get(id=id)
            return Dataset_File.objects.\
                filter(dataset__experiments__id=id).\
                values_list('id', flat=True)
        except Experiment.DoesNotExist:
            self.stderr.write('Experiment %s does not exist\n' % id)
            return []

    def _set_destination(self, destName):
        if not destName: 
            if not settings.DEFAULT_MIGRATION_DESTINATION:
                raise CommandError("No default destination configured")
            destName = settings.DEFAULT_MIGRATION_DESTINATION
        try:
            self.dest = Destination.get_destination(destName)
        except MigrationError as e:
            raise CommandError("Migration error: %s" % e.args[0])
        except ValueError:
            raise CommandError("Destination %s not known" % destName)

    def _list_destinations(self):
        for dest in settings.MIGRATION_DESTINATIONS:
            self.stdout.write('{0:<16} : {1:} : {2:}\n'.
                              format(dest['name'], dest['transfer_type'],
                                     dest['base_url']))

    def _score_all_datafiles(self):
        scores = self._do_score_all()
        total = 0
        for entry in scores:
            datafile = entry[0]
            try:
                total += int(datafile.size)
            except:
                pass
            self.stdout.write("datafile %s / %s, size = %s, " \
                              "score = %s, total_size = %d\n" % \
                                  (datafile.url, datafile.id, 
                                   datafile.size, entry[1], total)) 
            
    def _reclaim(self, args):
        if len(args) != 1:
            raise CommandError("Reclaim subcommand requires an argument")
        try:
            required_amount = int(args[0])
        except:
            raise CommandError("reclaim argument must be an integer")
        scores = self._do_score_all()
        total = 0
        for entry in scores:
            if total >= required_amount:
                break
            datafile = entry[0]
            if self.verbosity > 1:
                if self.dryRun:
                    self.stdout.write("Would have migrated %s / %s " \
                                          "saving %s bytes\n" % \
                                          (datafile.url, datafile.id, 
                                           datafile.size))
                else:
                    self.stdout.write("Migrating %s / %s saving %s bytes\n" % \
                                          (datafile.url, datafile.id, 
                                           datafile.size))
            total += int(datafile.size) 
            if not self.dryRun:
                migrate_datafile(datafile, self.dest)
        if self.dryRun:
            self.stdout.write("Would have reclaimed %d bytes\n" % total)
        else:
            self.stdout.write("Reclaimed %d bytes\n" % total)

    def _do_score_all(self):
        scorer = MigrationScorer(settings.MIGRATION_SCORING_PARAMS)
        return scorer.score_all_datafiles()
