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
    migrate_datafile_by_id
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
        '    destinations          : lists the recognized destinations' 
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dest',
                    action='store',
                    dest='dest',
                    default=settings.DEFAULT_MIGRATION_DESTINATION,
                    help='The destination for the transfer. ' \
                        'The default destination is %s' % \
                        settings.DEFAULT_MIGRATION_DESTINATION), 
        )

    def handle(self, *args, **options):
        verbose = options['verbosity'] > 1
        if len(args) == 0:
            raise CommandError("Expected a subcommand")
        subcommand = args[0]
        if subcommand == 'destinations':
            self._list_destinations()
            return
        args = args[1:]
        dest = self._get_destination(options['dest'])
        if not dest:
            return
        if subcommand == 'datafile' or subcommand == 'datafiles': 
            ids = self._check_datafile_ids(args)
        elif subcommand == 'dataset' or subcommand == 'datasets':
            ids = []
            for id in args:
                ids.extend(self._ids_for_dataset(id))
        elif subcommand == 'experiment' or subcommand == 'experiments':
            ids = []
            for id in args:
                ids.extend(self._ids_for_experiment(id))
        else:
            raise CommandError("Unrecognized subcommand: %s" % subcommand)

        if len(args) == 0:
            raise CommandError("Expected one or more ids after the subcommand")
        elif len(ids) == 0:
            raise CommandError("No Datafiles selected")

        for id in ids:
            try:
                migrate_datafile_by_id(id, dest)
                if verbose:
                    self.stderr.write('Migrated datafile %s\n' % id)
            except Dataset_File.DoesNotExist:
                self.stderr.write('Datafile %s does not exist\n' % id)
            except MigrationError as e:
                self.stderr.write( \
                    'Migration failed for datafile %s : %s\n' % \
                        (id, e.args[0]))
        
    def _check_datafile_ids(self, ids):
        res = []
        for id in ids:
            try:
                Dataset_File.objects.get(id=id)
                res.append(id)
            except Dataset_File.DoesNotExist:
                self.stderr.write('Datafile %s does not exist\n' % id)
        return res

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
            print dest['name']
