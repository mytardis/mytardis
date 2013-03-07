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

import sys, re
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.log import dictConfig

from tardis.tardis_portal.util import get_free_space
from tardis.tardis_portal.models import Replica, Location

from tardis.apps.migration import MigrationError, \
    MigrationScorer, migrate_replica
from tardis.tardis_portal.logging_middleware import LOGGING

class Command(BaseCommand):
    args = '<subcommand> <arg> ...'
    help = 'This command migrates file Replicas for MyTardis Experiments, ' \
        'Datasets and Datafiles from one location to another.  The ' \
        'individual Replicas are migrated atomically, but there are no ' \
        'guarantees of atomicity at the Dataset or Experiment level.  The ' \
        'following subcommands are supported:\n' \
        '    migrate [<target> <id> ...] : migrates <target> replicas \n' \
        '    mirror [<target> <id> ...]  : copies <target> replicas without\n' \
        '                                  deleting the originals\n' \
        '    ensure <N>                  : migrates replicas to ensure N \n' \
        '                                  bytes of free space\n' \
        '    reclaim <N>                 : migrate replicas to reclaim N \n' \
        '                                  bytes of space\n' \
        '    score                       : score and list all datafiles\n' \
        '    destinations                : lists the recognized destinations\n' \
        'where <target> is "datafile", "dataset" or "experiment", and the ' \
        '<id>s are the mytardis numeric ids for the respective objects\n' 

    option_list = BaseCommand.option_list + (
        make_option('-a', '--all',
                    action='store_true',
                    dest='all',
                    help='Process all datafiles'), 
        make_option('-s', '--source',
                    action='store',
                    dest='source',
                    help='The destination for the transfer. ' \
                        'The default destination is %s' % \
                        settings.DEFAULT_MIGRATION_DESTINATION), 
        make_option('-d', '--dest',
                    action='store',
                    dest='dest',
                    help='The source for the transfer. ' \
                        'The default source is "local"'), 
        make_option('-n', '--dryRun',
                    action='store_true',
                    dest='dryRun',
                    default=False,
                    help='Dry-run mode just lists the replicas that' \
                        ' would be migrated / restored'), 
        make_option('--noRemove',
                    action='store_true',
                    dest='noRemove',
                    default=False,
                    help='No-remove mode migrates without removing' \
                        ' the actual file corresponding to the' \
                        ' source replica') 
        )

    conf = dictConfig(LOGGING)

    def handle(self, *args, **options):
        from tardis.tardis_portal.models import \
            Dataset_File, Dataset, Experiment

        self.verbosity = options.get('verbosity', 1)
        self.noRemove = options.get('noRemove', False)
        self.dryRun = options.get('dryRun', False)
        self.dest = self._get_destination(
            options.get('dest', None),
            settings.DEFAULT_MIGRATION_DESTINATION)
        self.source = self._get_destination(
            options.get('source', None), 'local')

        all = options.get('all', False)
        if len(args) == 0:
            raise CommandError("Expected a subcommand")
        subcommand = args[0]
        if subcommand == 'destinations':
            self._list_destinations()
            return
        elif subcommand == 'score':
            if self.source:
                self._score_all_datafiles()
            return
        args = args[1:]
        if not self.source or not self.dest:
            return
        if self.verbosity > 3:
            self.stderr.write('Source %s destination %s\n' % \
                                  (self.source.name, self.dest.name))
        if subcommand == 'reclaim':
            if not self.source.name == 'local':
                raise CommandError("Can only 'reclaim' for source 'local'")
            self._reclaim(args)
        elif subcommand == 'ensure':
            if not self.source.name == 'local':
                raise CommandError("Can only 'ensure' for source 'local'")
            self._ensure(args)
        elif subcommand == 'migrate' or subcommand == 'mirror' :
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
            self._process_datafile(id, subcommand)

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
            replica = Replica.objects.get(datafile_id=id,
                                          location=self.source)
            if subcommand == 'migrate':
                ok = migrate_replica(replica, self.dest,
                                     noRemove=self.noRemove)
            elif subcommand == 'mirror':
                ok = migrate_replica(replica, self.dest, mirror=True)
            if self.verbosity > 1:
                if ok: 
                    self.stdout.write('%s datafile %s\n' % \
                                          (self._verb(subcommand), id))
                elif self.verbosity > 2:
                    self.stdout.write('Did not %s datafile %s\n' % \
                                          (subcommand, id))
        except Replica.DoesNotExist:
            if self.verbosity > 2:
                self.stderr.write('No replica of %s exists at %s\n' % \
                                      (id, self.source.name))
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

    def _get_destination(self, destName, default):
        if not destName:
            if not default:
                raise CommandError("No default destination configured")
            else:
                destName = default
        try:
            dest = Location.get_location(destName)
            if not dest:
                raise CommandError("Destination %s not known" % destName)
            return dest
        except MigrationError as e:
            raise CommandError("Migration error: %s" % e.args[0])

    def _list_destinations(self):
        for loc in Location.objects.all():
            self.stdout.write('{0:<16} : {1:<8} : {2:<8} : {3:}\n'.
                              format(loc.name, loc.type, 
                                     loc.transfer_provider, loc.url))

    def _score_all_datafiles(self):
        scores = self._do_score_all()
        total = 0
        for entry in scores:
            datafile, replica, score = entry
            try:
                total += int(datafile.size)
            except:
                pass
            self.stdout.write("datafile %s / %s, size = %s, " \
                              "score = %s, total_size = %d\n" % \
                                  (replica.url, datafile.id, 
                                   datafile.size, score, total)) 
            
    def _reclaim(self, args):
        required_space = self._parse_amount(args)
        self._do_reclaim(required_space)

    def _ensure(self, args):
        required_space = self._parse_amount(args)
        free_space = get_free_space(settings.FILE_STORE_PATH)
        if free_space < required_space:
            self._do_reclaim(required_space - free_space)

    def _parse_amount(self, args):
        if len(args) < 1:
            raise CommandError("missing <amount> argument")
        elif len(args) > 1:
            raise CommandError("multiple <amount> arguments")
        pat = re.compile(r"^(\d+(?:\.\d+)?)([kmgtKMGT]?)$")
        res = pat.match(args[0])
        if res:
            amount = float(res.group(1))
            scale = res.group(2).lower()
            factor = {'': 1, 'k': 1024, 'm': 1048576,
                      'g': 1073741824, 't': 1099511627776}.get(scale)
            amount = amount * factor
            return long(amount)
        else:
            raise CommandError("<amount> argument (%s) must be a non-negative" \
                               " number followed  by an optional scale" \
                               " factor (K, M, G or T)" % args[0])
    
    def _do_reclaim(self, required):
        scores = self._do_score_all()
        total = 0
        for entry in scores:
            if total >= required:
                break
            datafile, replica, _ = entry
            if self.verbosity > 1:
                if self.dryRun:
                    self.stdout.write("Would have migrated %s / %s " \
                                          "saving %s bytes\n" % \
                                          (replica.url, datafile.id, 
                                           datafile.size))
                else:
                    self.stdout.write("Migrating %s / %s saving %s bytes\n" % \
                                          (replica.url, datafile.id, 
                                           datafile.size))
            total += int(datafile.size) 
            if not self.dryRun:
                migrate_replica(replica, self.dest)
        if self.dryRun:
            self.stdout.write("Would have reclaimed %d bytes\n" % total)
        else:
            self.stdout.write("Reclaimed %d bytes\n" % total)

    def _do_score_all(self):
        scorer = MigrationScorer(self.source.id,
                                 settings.MIGRATION_SCORING_PARAMS)
        return scorer.score_all_datafiles()
