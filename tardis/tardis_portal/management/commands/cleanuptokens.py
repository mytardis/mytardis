"""
Management utility to clean up tokens
"""

import sys

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from tardis.tardis_portal.models import Token, ExperimentACL
from tardis.tardis_portal.auth.token_auth import TokenGroupProvider

from datetime import datetime as dt


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--delete-acls', dest='delete_acls', default=False,
            action='store_true',
            help='Delete orphaned ACLs related to tokens'),
    )

    help = 'Used to do some token housekeeping'

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', 1))
        delete_acls = options.get('delete_acls')

        expired_tokens = Token.objects.filter(expiry_date__lt=dt.today())
        num_tokens = expired_tokens.count()
        expired_tokens.delete()

        if verbosity > 0:
            self.stdout.write("%s Tokens cleaned up successfully\n" % num_tokens)

        if delete_acls:
            self._delete_unused_token_acls(verbosity)


    def _delete_unused_token_acls(self, verbosity):
        """
            delete ACLs if they are not in use
        """

        acls_to_delete = ExperimentACL.objects.filter(pluginId=TokenGroupProvider.name) \
                        .annotate(num_tokens=Count('experiment__token')) \
                        .filter(num_tokens__eq=0)

        num_acls = acls_to_delete.count()

        acls_to_delete.delete()

        if verbosity > 0:
            self.stdout.write("%s Token ACLs cleaned up successfully\n" % num_acls)
