"""
Management command to migrate datafiles, datasets and experiments
"""

import sys
import traceback
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, DEFAULT_DB_ALIAS
from tardis.tardis_portal.models import Experiment, Dataset, Dataset_File
from tardis.tardis_portal.models import Author_Experiment, ExperimentACL
from tardis.tardis_portal.models import ExperimentParameterSet, ExperimentParameter
from tardis.tardis_portal.models import DatasetParameterSet
from tardis.tardis_portal.models import DatafileParameterSet

DEFAULT_MIGRATION_DESTINATION = 'test'

class Command(BaseCommand):
    args = '<subcommand> <arg> ...'
    help = 'This command performs migrates files for MyTardis Experiments, ' \
        'Datasets and Datafiles to configured secondary file stores.  The ' \
        'following subcommands are supported:\n' \
        '    datafile <id> ...     : migrates files for datafiles\n' \
        '    dataset <id> ...      : migrates files for datasets\n' \
        '    experiment <id> ...   : migrates files for experiments\n' \
        '    destinations          : lists the recognized destinations' 
    option_list = BaseCommand.option_list + (
        make_option('--dest',
                    action='store',
                    dest='dest',
                    default=False,
                    help='The destination for the transfer. ' \
                        'The default destination is %s' % \
                        DEFAULT_MIGRATION_DESTINATION),
        )

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("Expected a subcommand")
        try:
            dest = Destination(options['dest'])
        except ValueError:
            raise CommandError("Destination %s not recognized" % \
                                   options['dest'])
        if args[0] == 'datafile':
            for id in args[1:]:
                try:
                    migrate_datafile_by_id(id, dest)
                    print('Migrated datafile %s' % id)
                except MigrationError as e:
                    print('Migration failed for %s : %s' % (id, e.args[0]))
        else:
            raise CommandError("Unrecognized or unimplemented " \
                                   "subcommand: %s" % args[0])
        
