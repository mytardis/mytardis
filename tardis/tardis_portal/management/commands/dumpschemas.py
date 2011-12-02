"""
 Command for dumping soft schema definitions
"""
import sys
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.core import serializers

from optparse import make_option

from tardis.tardis_portal import models


class Command(BaseCommand):
    args = "[namespace...]"
    help = "Dump soft schema definitions.  No namespace = dump all schemas"

    option_list = BaseCommand.option_list + (
        make_option('--format', default='json', dest='format',
                    help='Specifies the output serialization format.'),
        make_option('--database', action='store', dest='database',
                    default=DEFAULT_DB_ALIAS,
                    help='Nominates a specific database'),
        )

    def handle(self, *args, **options):
        using = options.get('database', DEFAULT_DB_ALIAS)
        connection = connections[using]
        show_traceback = options.get('traceback', False)
        format = options.get('format', 'json')
        if format not in serializers.get_public_serializer_formats():
            raise CommandError("Unknown serialization format: %s" % format)

        try:
            serializers.get_serializer(format)
        except KeyError:
            raise CommandError("Unknown serialization format: %s" % format)

        objects = []
        if len(args) == 0:
            objects.extend(models.Schema.objects.all())
            objects.extend(models.ParameterName.objects.all())
        else:
            schemas = models.Schema.objects.filter(namespace__in=args)
            if len(schemas) == 0:
                raise CommandError('No schemas found')
            schema_set = set([s.namespace for s in schemas])
            arg_set = set(args)
            skipped = arg_set - schema_set
            if len(skipped) > 0:
                sys.stderr.write('Schema not found: {0}\n'.format( \
                    ', '.join(skipped)))
            objects.extend(schemas)
            objects.extend(models.ParameterName.objects.filter(schema__namespace__in=args))
        try:
            return serializers.serialize(format, objects, indent=4,
                        use_natural_keys=True)
        except Exception, e:
            if show_traceback:
                raise
            raise CommandError("Unable to serialize database: %s" % e)
