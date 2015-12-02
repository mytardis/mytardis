"""
Management utility to clean up tokens
"""

from datetime import datetime as dt

from optparse import make_option
from django.core.management.base import BaseCommand
from django.db.models import Count
from tardis.tardis_portal.models import Token, ObjectACL
from tardis.tardis_portal.auth.token_auth import TokenGroupProvider


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--keep-acls', dest='keep_acls', default=False,
            action='store_true',
            help='Keep orphaned token ACLs'),
    )

    help = 'Deletes unused tokens and optionally their ACLs'

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', 1))
        keep_acls = options.get('keep_acls')

        expired_tokens = Token.objects.filter(expiry_date__lt=dt.today())
        num_tokens = expired_tokens.count()
        expired_tokens.delete()

        if verbosity > 0:
            self.stdout.write("%s Tokens cleaned up successfully\n" % num_tokens)

        if not keep_acls:
            self._purge_unused_token_acls(verbosity)


    def _purge_unused_token_acls(self, verbosity):
        """
            purge ACLs if they are not in use
        """

        acls_to_delete = ObjectACL.objects.filter(
            pluginId=TokenGroupProvider.name).annotate(
                num_tokens=Count('content_object__token')
            ).filter(num_tokens__eq=0)

        num_acls = acls_to_delete.count()

        acls_to_delete.delete()

        if verbosity > 0:
            self.stdout.write("%s Token ACLs cleaned up successfully\n" % num_acls)
