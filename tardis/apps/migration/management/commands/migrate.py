"""
Management command to migrate datafiles, datasets and experiments
"""

import sys
import traceback
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
        make_option('-v', '--verbose',
                    action='store_true',
                    dest='verbose',
                    help='Produce output for each Datafile migrated')
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        if len(args) == 0:
            raise CommandError("Expected a subcommand")
        subcommand = args[0]
        if subcommand == 'destinations':
            self._list_destinations()
            return
        if len(args) == 1:
            raise CommandError("Expected one or more ids after the subcommand")
        args = args[1:]
        dest = self._get_destination(options['dest'])
        if not dest:
            return
        if subcommand == 'datafile' or subcommand == 'datafiles': 
            ids = args
        elif subcommand == 'dataset' or subcommand == 'datasets':
            ids = []
            for id in args:
                ids.extend(self._ids_for_dataset(id))
        elif subcommand == 'experiment' or subcommand == 'experiments':
            ids = []
            for id in args:
                ids.extend(self._ids_for_experiment(id))
        else:
            raise CommandError("Unrecognized or unimplemented " \
                                   "subcommand: %s" % args[0])
        print ids
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
                value_list('id', flat=True)
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
