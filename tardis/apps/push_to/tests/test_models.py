from django.contrib.auth.models import User, Group
from django.test import TestCase
from paramiko import PKey, RSAKey

from tardis.apps.push_to.models import Credential, RemoteHost, OAuthSSHCertSigningService


class ModelsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('aperson', email='abc@example.com', password='abc')
        self.user2 = User.objects.create_user('anotherperson', email='def@example.com', password='abc')
        self.user3 = User.objects.create_user('yetanotherperson', email='ghi@example.com', password='abc')
        self.group = Group.objects.create(name='test group')
        self.group.user_set.add(self.user2)
        self.group.user_set.add(self.user3)

    def test_credential_generation(self):
        remote_host = RemoteHost.objects.create(nickname='dummy host', host_name='localhost',
                                                administrator=self.user1)
        credential = Credential.generate_keypair_credential(self.user1, 'remote_user', remote_hosts=[remote_host])
        key = credential.key
        self.assertTrue(isinstance(key, PKey), 'The generated key pair is an instance of a paramiko PKey object')
        self.assertTrue(key.can_sign(), 'PKey object can sign (i.e. has private and public key parts)')

    def test_pkey_to_credential(self):
        key = RSAKey.generate(bits=2048)
        credential = Credential.objects.create(user=self.user1, remote_user='remote_user')
        credential.key = key
        credential.save()
        credential_copy = Credential.objects.get(pk=credential.pk)
        self.assertEqual(key.get_fingerprint(), credential_copy.key.get_fingerprint())

    def test_get_allowed_signing_services(self):
        svc_for_all = OAuthSSHCertSigningService.objects.create(nickname='Service for everyone',
                                                                oauth_authorize_url='https://localhost/authorize',
                                                                oauth_token_url='https://localhost/token',
                                                                oauth_check_token_url='https://localhost/check_token',
                                                                oauth_client_id='a client',
                                                                oauth_client_secret='a secret',
                                                                cert_signing_url='https://localhost/sign',
                                                                allow_for_all=True)

        svc_for_group = OAuthSSHCertSigningService.objects.create(nickname='Service for group',
                                                                  oauth_authorize_url='https://localhost/authorize',
                                                                  oauth_token_url='https://localhost/token',
                                                                  oauth_check_token_url='https://localhost/check_token',
                                                                  oauth_client_id='a client',
                                                                  oauth_client_secret='a secret',
                                                                  cert_signing_url='https://localhost/sign')
        svc_for_group.allowed_groups.add(self.group)

        svc_for_user = OAuthSSHCertSigningService.objects.create(nickname='Service for user',
                                                                 oauth_authorize_url='https://localhost/authorize',
                                                                 oauth_token_url='https://localhost/token',
                                                                 oauth_check_token_url='https://localhost/check_token',
                                                                 oauth_client_id='a client',
                                                                 oauth_client_secret='a secret',
                                                                 cert_signing_url='https://localhost/sign')
        svc_for_user.allowed_users.add(self.user1)

        u1_svcs = OAuthSSHCertSigningService.get_available_signing_services(self.user1)
        u2_svcs = OAuthSSHCertSigningService.get_available_signing_services(self.user2)
        u3_svcs = OAuthSSHCertSigningService.get_available_signing_services(self.user3)

        # All users should have access to svc_for_all
        self.assertEqual(u1_svcs.filter(pk=svc_for_all.pk).count(), 1)
        self.assertEqual(u2_svcs.filter(pk=svc_for_all.pk).count(), 1)
        self.assertEqual(u3_svcs.filter(pk=svc_for_all.pk).count(), 1)

        # Users 2 and 3 should have access to svc_for_group, but not user 1
        self.assertEqual(u1_svcs.filter(pk=svc_for_group.pk).count(), 0)
        self.assertEqual(u2_svcs.filter(pk=svc_for_group.pk).count(), 1)
        self.assertEqual(u3_svcs.filter(pk=svc_for_group.pk).count(), 1)

        # Only user 1 should have access to svc_for_user
        self.assertEqual(u1_svcs.filter(pk=svc_for_user.pk).count(), 1)
        self.assertEqual(u2_svcs.filter(pk=svc_for_user.pk).count(), 0)
        self.assertEqual(u3_svcs.filter(pk=svc_for_user.pk).count(), 0)