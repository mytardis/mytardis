"""
 Command for loading soft schema definitions
"""
import sys

from django.core.management.base import BaseCommand
from django.db import connections, DEFAULT_DB_ALIAS
from django.core import serializers

from tardis.tardis_portal import models


class Command(BaseCommand):
    help = "Load soft schema definitions"
    args = "schema [schema ...]"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            'schemas',
            nargs='*',
            help=('Path(s) to one or more schema definition files, '
                  'e.g. tardis/tardis_portal/fixtures/jeol_metadata_schema.json')
        )

        # Named (optional) arguments
        parser.add_argument(
            '--database',
            default=DEFAULT_DB_ALIAS,
            dest='database',
            help='Nominates a specific database'
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            default=False,
            dest='replace',
            help=("Replace the schema and parameter names with the same pk.  "
                  "Warning: This will overwrite the entries with the same "
                  "primary keys, even if the entries don't match.")
        )

    def handle(self, *args, **options):
        using = options.get('database', DEFAULT_DB_ALIAS)

        connection = connections[using]

        verbosity = int(options.get('verbosity', 1))
        show_traceback = options.get('traceback', False)

        humanize = lambda dirname: dirname and "'%s'" % dirname or 'absolute path'

        formats = []
        schemas = options.get('schemas', [])
        for name in schemas:
            parts = name.split('.')
            format = parts[-1]
            if format in serializers.get_public_serializer_formats():
                self.stdout.write("Loading '%s' schema...\n" % name)
            else:
                self.stderr.write(
                    self.style.ERROR("Problem installing schema '%s': %s is not a known serialization format.\n" %
                        (name, format)))
                return

            try:
                full_path = name
                data = open(full_path)
                try:
                    objects = serializers.deserialize(format, data)
                    for obj in objects:
                        if not options.get('replace', False):
                            obj.object.pk = None
                        obj.save(using=using)
                except (SystemExit, KeyboardInterrupt):
                    raise
                except Exception:
                    import traceback
                    data.close()
                data.close()

            except Exception, e:
                self.stdout.write("No %s schema '%s' in %s.\n" % \
                                      (parts[-1], name, humanize(full_path)))
