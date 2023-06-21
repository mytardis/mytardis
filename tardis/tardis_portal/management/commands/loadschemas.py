"""
 Command for loading soft schema definitions
"""
from django.core import serializers
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS


class Command(BaseCommand):
    help = "Load soft schema definitions"
    args = "schema [schema ...]"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            "schemas",
            nargs="*",
            help=(
                "Path(s) to one or more schema definition files, "
                "e.g. tardis/tardis_portal/fixtures/jeol_metadata_schema.json"
            ),
        )

        # Named (optional) arguments
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            dest="database",
            help="Nominates a specific database",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            default=False,
            dest="replace",
            help=(
                "Replace the schema and parameter names with the same pk.  "
                "Warning: This will overwrite the entries with the same "
                "primary keys, even if the entries don't match."
            ),
        )

    def handle(self, *args, **options):
        using = options.get("database", DEFAULT_DB_ALIAS)

        def humanize(dirname):
            return "'%s'" % dirname if dirname else "absolute path"

        schemas = options.get("schemas", [])
        for name in schemas:
            parts = name.split(".")
            format = parts[-1]
            if format in serializers.get_public_serializer_formats():
                self.stdout.write("Loading '%s' schema...\n" % name)
            else:
                self.stderr.write(
                    self.style.ERROR(
                        "Problem installing schema '%s': %s is not a known serialization format.\n"
                        % (name, format)
                    )
                )
                return

            try:
                full_path = name
                with open(full_path, encoding="utf-8") as data:
                    try:
                        objects = serializers.deserialize(format, data)
                        for obj in objects:
                            if not options.get("replace", False):
                                obj.object.pk = None
                            obj.save(using=using)
                    except Exception as err:
                        if isinstance(err, (SystemExit, KeyboardInterrupt)):
                            raise
                        data.close()
                    data.close()

            except Exception:
                self.stdout.write(
                    "No %s schema '%s' in %s.\n"
                    % (parts[-1], name, humanize(full_path))
                )
