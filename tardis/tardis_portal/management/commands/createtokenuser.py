"""
Management utility to create a token user
"""

from optparse import make_option
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from tardis.tardis_portal.models import UserProfile, UserAuthentication


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default='tokenuser',
            help='Specifies the username for the tokenuser.'),
    )

    help = 'Used to create a MyTardis tokenuser.'

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', 1))
        username = options.get('username', None)
        email = 'noreply'
        password = None

        user = User.objects.create_user(username, email, password)
        user.userprofile.isDjangoAccount = False
        user.userprofile.save()

        # We do not create a UserAuthentication intentionally.
        # If we did, lookups to find the "TokenAuth" would fail

        if verbosity > 0:
            self.stdout.write("Tokenuser %s created successfully\n" % username)
            self.stdout.write("Ensure you have TOKEN_USERNAME='%s' in your settings file\n" % username)
