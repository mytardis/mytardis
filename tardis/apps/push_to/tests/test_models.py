from django.contrib.auth.models import User, Group
from django.test import TestCase
from paramiko import PKey, RSAKey

from ..models import Credential, RemoteHost, OAuthSSHCertSigningService


class ModelsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('aperson',
                                              email='abc@example.com',
                                              password='abc')
        self.user2 = User.objects.create_user('anotherperson',
                                              email='def@example.com',
                                              password='abc')
        self.user3 = User.objects.create_user('yetanotherperson',
                                              email='ghi@example.com',
                                              password='abc')
        self.group = Group.objects.create(name='test group')
        self.group.user_set.add(self.user2)
        self.group.user_set.add(self.user3)

    def test_credential_generation(self):
        remote_host = RemoteHost.objects.create(nickname='dummy host',
                                                host_name='localhost',
                                                administrator=self.user1)
        credential = Credential.generate_keypair_credential(
            self.user1, 'remote_user',
            remote_hosts=[remote_host])
        key = credential.key
        self.assertTrue(
            isinstance(key, PKey),
            'The generated key pair is an instance of a paramiko PKey object')
        self.assertTrue(
            key.can_sign(),
            'PKey object can sign (i.e. has private and public key parts)')

    def test_pkey_to_credential(self):
        key = RSAKey.generate(bits=2048)
        credential = Credential.objects.create(user=self.user1,
                                               remote_user='remote_user')
        credential.key = key
        credential.save()
        credential_copy = Credential.objects.get(pk=credential.pk)
        self.assertEqual(key.get_fingerprint(),
                         credential_copy.key.get_fingerprint())

    def test_key_type_detection(self):
        rsa_key_string = (
            'AAAAB3NzaC1yc2EAAAADAQABAAABAQC55qMy9V9u+kXvyQfeztFjzf0Mz7ieRit1'
            'lEaQLV9zn5AGGzametc8JGWIwWju3iBW0WIndkZltNmk3pdbAxl9S4gP3B9ga+5w'
            'J1fADaYOl8OmKOu/ovg1Jtll3wRhkI4L3cHAuoPjwOc1Erbj1VTnyZi0FrmsNBUJ'
            'yQdrf0Qge+lBXHUbccerObYX1JX+nAGlJkYMBKPJWfjdnj4ff5nNr0ZxutiB7FyG'
            'v+VRrGndbBRTCq19WF+NaHOSoNgwKnQYjAmDYXZ2O2q036y9tFYJ6BUma4qVV1hf'
            'gPcMFU9vZA/cXDE8WJxxZAzscztoGl97QQGKFnu7e7odat+/czRl')
        dsa_key_string = (
            'AAAAB3NzaC1kc3MAAACBANpiUkTHu88d1ldKC1p6NkWqMMLZ3y2Gk/jnwPEQVylw'
            'NmZoqpBU86TyPm5kNiuAEF9Jn3K2B8HfemaeSO6ZFsyIgEWyvs6nnVGccWhrVbc+'
            '74z8vayj7MjhisqA7xBFASGWjHoAumZXwicr9XIpTC6LYL01VU7dfMP49w4SByXZ'
            'AAAAFQDhxd00faq4j7wUP6tDFCQt/jWLNQAAAIEAm5ZhxzjP0nYRU8HqcqZP8TKd'
            'TWj+A6cInuL0eB1u4jIUeDFFGGz3H/bHaP86OkMVsXsHTwnAlBeAvfAaE5pux58k'
            'tgAdmaFdosn0RSlycAFTs3z2zeSBa9xC+8xs/RMIZu66Km+ut5OGgX5gu+z033BY'
            'OPuj08t0s4EIZmakFEAAAACAQi2LborZAIaWXX5SesRwYH8yNlB5wT4VNNt4Xmt0'
            'jC/KkM2Xb/WCesu+n+NxFFQfAnEYScZtFj7iIjX5LbqV+gyJi/+cU6IofMoBO7vS'
            'taP78YcfLGgYOGA3M7rofeBpj9eGlr6uKqqL3h+e3gxAtzjA6pRlmnUKRafUEEuD'
            'EsI=')

        credential = Credential.objects.create(user=self.user1,
                                               remote_user='remote_user')
        credential.public_key = rsa_key_string
        self.assertEqual(credential.key.get_name(), 'ssh-rsa')

        credential.key_type = None
        credential.public_key = 'ssh-rsa ' + rsa_key_string
        self.assertEqual(credential.key.get_name(), 'ssh-rsa')

        credential.key_type = None
        credential.public_key = dsa_key_string
        self.assertEqual(credential.key.get_name(), 'ssh-dss')

        credential.key_type = None
        credential.public_key = 'ssh-dss ' + dsa_key_string
        self.assertEqual(credential.key.get_name(), 'ssh-dss')

    def test_get_allowed_signing_services(self):
        svc_for_all = OAuthSSHCertSigningService.objects.create(
            nickname='Service for everyone',
            oauth_authorize_url='https://localhost/authorize',
            oauth_token_url='https://localhost/token',
            oauth_check_token_url='https://localhost/check_token',
            oauth_client_id='a client',
            oauth_client_secret='a secret',
            cert_signing_url='https://localhost/sign',
            allow_for_all=True)

        svc_for_group = OAuthSSHCertSigningService.objects.create(
            nickname='Service for group',
            oauth_authorize_url='https://localhost/authorize',
            oauth_token_url='https://localhost/token',
            oauth_check_token_url='https://localhost/check_token',
            oauth_client_id='a client',
            oauth_client_secret='a secret',
            cert_signing_url='https://localhost/sign')
        svc_for_group.allowed_groups.add(self.group)

        svc_for_user = OAuthSSHCertSigningService.objects.create(
            nickname='Service for user',
            oauth_authorize_url='https://localhost/authorize',
            oauth_token_url='https://localhost/token',
            oauth_check_token_url='https://localhost/check_token',
            oauth_client_id='a client',
            oauth_client_secret='a secret',
            cert_signing_url='https://localhost/sign')
        svc_for_user.allowed_users.add(self.user1)

        u1_svcs = OAuthSSHCertSigningService.get_available_signing_services(
            self.user1)
        u2_svcs = OAuthSSHCertSigningService.get_available_signing_services(
            self.user2)
        u3_svcs = OAuthSSHCertSigningService.get_available_signing_services(
            self.user3)

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
