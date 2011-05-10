"""
 Command for dumping soft schema definitions
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.core import serializers

from optparse import make_option

from tardis.tardis_portal import models


class Command(BaseCommand):
    help = "Dump soft schema definitions"

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
        objects.extend(models.Schema.objects.all())
        objects.extend(models.ParameterName.objects.all())
        try:
            return serializers.serialize(format, objects, indent=4,
                        use_natural_keys=True)
        except Exception, e:
            if show_traceback:
                raise
            raise CommandError("Unable to serialize database: %s" % e)
