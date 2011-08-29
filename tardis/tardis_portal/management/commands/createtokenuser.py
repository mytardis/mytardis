"""
Management utility to create a token user
"""

from optparse import make_option
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from tardis.tardis_portal.models import UserProfile, UserAuthentication
from tardis.tardis_portal.auth.token_auth import auth_key as tokenauth_key


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default='tokenuser',
            help='Specifies the username for the tokenuser.'),
    )

    help = 'Used to create a MyTARDIS tokenuser.'

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', 1))
        username = options.get('username', None)
        email = 'noreply'
        password = None

        user = User.objects.create_user(username, email, password)
        userProfile = UserProfile(user=user, isDjangoAccount=False)
        userProfile.save()

        authentication = UserAuthentication(userProfile=userProfile,
                                            username=username,
                                            authenticationMethod=tokenauth_key)
        authentication.save()

        if verbosity > 0:
            self.stdout.write("Tokenuser %s created successfully\n" % username)
