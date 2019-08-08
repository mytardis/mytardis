from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import User, Permission
from django.conf import settings
from ...models import UserProfile, UserAuthentication
import ldap
class Command(BaseCommand):

    help = 'Add a specific user from LDAP'                                                                        
    def add_arguments(self, parser):
        parser.add_argument('user_id', nargs='+', type=str) 

    def gen_random_password(self):
        import random
        random.seed()
        characters = 'abcdefghijklmnopqrstuvwxyzABCDFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?'
        passlen = 16
        password = "".join(random.sample(characters,passlen))
        return password

    def handle(self, *args, **options):
        l = ldap.initialize(settings.LDAP_URL)
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(settings.LDAP_ADMIN_USER, settings.LDAP_ADMIN_PASSWORD)
        total = 0
        total_created = 0
        ldap_dict = settings.LDAP_USER_ATTR_MAP
        first_name_key = 'givenName'
        last_name_key = 'sn'
        email_key = 'mail'
        for key in ldap_dict.keys():
            test_value = ldap_dict[key]
            if test_value == "first_name":
                first_name_key = key
            elif test_value == "last_name":
                last_name_key = key
            elif test_value  == "email":
                email_key = key
        for user_id in options['user_id']:
            print("Looking up {}".format(user_id))
            results = l.search_s(settings.LDAP_USER_BASE, ldap.SCOPE_SUBTREE, "({0}={1})".format(settings.LDAP_USER_LOGIN_ATTR, user_id))
            
            for e, r in results:
                username = r[settings.LDAP_USER_LOGIN_ATTR][0].decode('utf-8')
                first_name = r[first_name_key][0].decode('utf-8')
                last_name = r[last_name_key][0].decode('utf-8')
                email = r[email_key][0].decode('utf-8')
                user, created = User.objects.get_or_create(username=username, email=email, first_name=first_name, last_name=last_name)
                total += 1
                if created:
                    user.set_password(self.gen_random_password())
                    user.user_permissions.add(Permission.objects.get(codename='add_experiment'))
                    user.user_permissions.add(Permission.objects.get(codename='add_dataset'))
                    user.user_permissions.add(Permission.objects.get(codename='add_datafile'))
                    user.save()
                    authentication = UserAuthentication(userProfile=user.userprofile,
                                                        username=username,
                                                        authenticationMethod=settings.LDAP_METHOD)
                    authentication.save()
                    total_created += 1
                    print("Added {}".format(user_id))
                else:
                    print("{} already exists".format(user_id))
    print("Found {}/{} users, added {}".format(total, len(options['user_id']), total_created))
