"""
 Command for dumping soft schema definitions
"""
import sys

from django.core.management.base import BaseCommand
from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.core import serializers

from optparse import make_option

from tardis.tardis_portal import models


class Command(BaseCommand):
    help = "Dump soft schema definitions"
    args = "schema [schema ...]"

    option_list = BaseCommand.option_list + (
        make_option('--database', action='store', dest='database',
                    default=DEFAULT_DB_ALIAS,
                    help='Nominates a specific database'),
        )

    def handle(self, *args, **options):
        using = options.get('database', DEFAULT_DB_ALIAS)

        connection = connections[using]

        verbosity = int(options.get('verbosity', 1))
        show_traceback = options.get('traceback', False)

        # commit is a stealth option - it isn't really useful as
        # a command line option, but it can be useful when invoking
        # loaddata from within another script.
        # If commit=True, loaddata will use its own transaction;
        # if commit=False, the data load SQL will become part of
        # the transaction in place when loaddata was invoked.
        commit = options.get('commit', True)

        humanize = lambda dirname: dirname and "'%s'" % dirname or 'absolute path'

        # Start transaction management. All fixtures are installed in a
        # single transaction to ensure that all references are resolved.
        if commit:
            transaction.commit_unless_managed(using=using)
            transaction.enter_transaction_management(using=using)
            transaction.managed(True, using=using)

        formats = []
        for name in args:
            parts = name.split('.')
            format = parts[-1]
            if format in serializers.get_public_serializer_formats():
                self.stdout.write("Loading '%s' schema...\n" % name)
            else:
                self.stderr.write(
                    self.style.ERROR("Problem installing schema '%s': %s is not a known serialization format.\n" %
                        (name, format)))
                if commit:
                    transaction.rollback(using=using)
                    transaction.leave_transaction_management(using=using)
                return

            try:
                full_path = name
                data = open(full_path)
                try:
                    objects = serializers.deserialize(format, data)
                    for obj in objects:
			obj.save(using=using)
                except (SystemExit, KeyboardInterrupt):
                    raise
                except Exception:
                    import traceback
                    data.close()
                    if commit:
                        transaction.rollback(using=using)
                        transaction.leave_transaction_management(using=using)
                        if show_traceback:
                            traceback.print_exc()
                        else:
                            self.stderr.write(
                                self.style.ERROR("Problem installing schema '%s': %s\n" %
                                                 (full_path, ''.join(traceback.format_exception(sys.exc_type,
                                                                                                sys.exc_value, sys.exc_traceback)))))
                        return

                data.close()

            except Exception, e:
                self.stdout.write("No %s schema '%s' in %s.\n" % \
                                      (parts[-1], name, humanize(full_path)))


        if commit:
            transaction.commit(using=using)
            transaction.leave_transaction_management(using=using)
            connection.close()
