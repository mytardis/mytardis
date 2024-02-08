"""
 Command for dumping soft schema definitions
"""
import sys

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS

from ... import models


class Command(BaseCommand):
    args = "[namespace...]"
    help = "Dump soft schema definitions.  No namespace = dump all schemas"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("namespaces", nargs="*")

        # Named (optional) arguments
        parser.add_argument(
            "--format",
            default="json",
            dest="format",
            help="Specifies the output serialization format.",
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            dest="database",
            help="Nominates a specific database",
        )

    def handle(self, *args, **options):
        namespaces = options.get("namespaces", [])
        show_traceback = options.get("traceback", False)
        format = options.get("format", "json")
        if format not in serializers.get_public_serializer_formats():
            raise CommandError("Unknown serialization format: %s" % format)

        try:
            serializers.get_serializer(format)
        except KeyError:
            raise CommandError("Unknown serialization format: %s" % format)

        objects = []
        if not namespaces:
            objects.extend(models.Schema.objects.all())
            objects.extend(models.ParameterName.objects.all())
        else:
            schemas = models.Schema.objects.filter(namespace__in=namespaces)
            if not schemas:
                raise CommandError("No schemas found")
            schema_set = set(s.namespace for s in schemas)
            arg_set = set(args)
            skipped = arg_set - schema_set
            if skipped:
                sys.stderr.write("Schema not found: {0}\n".format(", ".join(skipped)))
            objects.extend(schemas)
            objects.extend(
                models.ParameterName.objects.filter(schema__namespace__in=args)
            )
        try:
            return serializers.serialize(
                format, objects, indent=4, use_natural_foreign_keys=True
            )
        except Exception as e:
            if show_traceback:
                raise
            raise CommandError("Unable to serialize database: %s" % e)
