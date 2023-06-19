from django.contrib.auth.models import Group, User
from django.test import TestCase

from paramiko import PKey, RSAKey

from ..models import Credential, OAuthSSHCertSigningService, RemoteHost


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

    def test_keys_from_private_key_only(self):
        rsa_private_key = '''-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAsCx+Qxl+fDkygxeSVHdDgS0MBoh0vtisGjiM3WlIAyQ4a/oK
U0ztkOrK60RaYrkxw5X2sTQqa/EFLd7PwIK22B4fG7kJ4w1HyL7g6lP2YLDzKOvv
35NExET/1HQKTh8D11efxQIqz+5yHfX7xuWGbcbSwq+QbYHSHKIwmUbH9876P4KA
Pxja+bJcUvOsJVUtOWNojtLtUFlJaagsc1o4f48nQ6rk+PWj9QXp8qMmTOnYmqjW
gCeyQlW5cZ0VgFnaAe0/rfEs6X6dr9o+/p6nyvABdZFXkWgKaq8UNvmzGT4FEWj+
+GFihZ817xWw+a83rAXwa7zshSkOiM4WM9E+OQIDAQABAoIBAEOr85wmsNVayzJb
3ZOgdEesXBAuXlnotMMlscZi6Ix8X0fqtgilZiPibKvOh8GgTaNJeYc7+IeZ/1lN
WxQhocaGW4C0pT2YHljYKWEZe2xMzDqN1ohU83dI4dRj9olnlHwlZnOwj21rtF4Z
3Orbw7VrSA4MjjfiRClHi890xt9C+IGEey2tO6XykhJ5F86Sl3gQDspvVJABpQy1
tpji+lty/bxE2GMD3m4jUhwPDO/cgEbGVWHCtwgY/d9CzWBn9ArSRoh1ZxpRCjl1
uoqnII822S6Jmx0Yt7AFykplhjUYlDbbW4HY5tWf4nkXnSA29/4tZM8dAqn0VDQ5
Hagh8pkCgYEA4/cU7GyF/oNvO27bsCv89y26r0pwzSNXZe4BSoM3cP0m6AwiJZl1
CsrO3RHGlY1UzccxaSf7WgDdVp4EimUtCb5c/lL1brCmkPptFdjSvkBCgKkNzxAE
cHcsMEt/9D4b/fXCmIqjQFw1yag/cwrdZbHgRz8v5wk2wgOech6WRdsCgYEAxdbj
iIh5/n8bcq59cy5XrpCDvV7XpsMVKKFPmNXnUUHhRNuzP4wfTgjczl1CkqvW2yj7
xI4CEsqsVKsdkhcdOs8knEf3sz389VrmhSzbeqxic0J9NiXeJyIXdZ9e+VfR5rwl
IBDVIRlL4/qWUOPbMbLTkJmbgTFvyRZuCl9jansCgYBj68taDf91nbrFvEPDJqTM
21h2uRRUdmc6oGYkePt2JSBGmfrlrCvnPRoLQF1g8//16pe31fSQcMyTyNOIrexd
1vj/6PD3Qarg5UOnTdCh35zGtFL/LbAkc7gEuzMspYSzfmN7ZVlFPqW87GhTTrHY
f20lDYc7p4g+5kMvFkUb/QKBgEH9X3/XJfoBo8Io+adFufF8OrUbwYraX2BiDg7I
qpOsCdvR/IQh1P9ObXhYGzCZKN2JWhFB3OcvuzOyr/Zex10qYufOCY08C/g7DdE2
GS9d+KjBcMpy7xrWgES3mBJLfLQd5bRAaRbVPT8aArGQjziQkYkV84ywVL0aQjIr
hxmpAoGAXBJHxQbm58Lx67cz4ncM2biwitZkRAXsgRX0A3YKQQ9f4o7KPc+KwpZJ
YJAyP9BHbsF01C9RB0dlNf+HevuaIv9hhjgALvC2qGHCJ/CpCAlwTtaX5Zvv5isw
dDxp+xLsgZL+zO6iz+PO6+4KWEr1KZJFoQFk7kPiQk4ny4vchrI=
-----END RSA PRIVATE KEY-----'''
        rsa_public_key = (
            'AAAAB3NzaC1yc2EAAAADAQABAAABAQCwLH5DGX58OTKDF5JUd0OBLQwGiHS+2Kwa'
            'OIzdaUgDJDhr+gpTTO2Q6srrRFpiuTHDlfaxNCpr8QUt3s/AgrbYHh8buQnjDUfI'
            'vuDqU/ZgsPMo6+/fk0TERP/UdApOHwPXV5/FAirP7nId9fvG5YZtxtLCr5BtgdIc'
            'ojCZRsf3zvo/goA/GNr5slxS86wlVS05Y2iO0u1QWUlpqCxzWjh/jydDquT49aP1'
            'BenyoyZM6diaqNaAJ7JCVblxnRWAWdoB7T+t8Szpfp2v2j7+nqfK8AF1kVeRaApq'
            'rxQ2+bMZPgURaP74YWKFnzXvFbD5rzesBfBrvOyFKQ6IzhYz0T45'
        )

        dsa_private_key = '''-----BEGIN DSA PRIVATE KEY-----
MIIBvAIBAAKBgQDzqGnavKUd93iFcg2Th79yW89MZRnJBihdho/0PkbnaYklj5tZ
oLYVs1jTL/FwAQcermRhrwuPBAsavfG+mkQgPAteirWSfEd+zamntePVV56GwJtb
8zwjXgun/mvvduNgQ12wr6/zni8D06oC3sFfOQgcAUwIAN7Of8JFGu5rFQIVAPZd
1GaH/nstAH1fjyR8dVDGqwhlAoGAWhlb+9Zweto/+g1RIv6AmiNmvmGzkzcXEdLN
5P/N+wxD4/zLU1ljZoy+SYsCPQP6Fp+JeNK+mFigA6uiNzAi14RsDiZZIwEzVG7/
TepJfAMiu3fcrUPXA2KPZXs3hvS+nyaJBqbfOgcRCRqmawYKqnt7tUysyK37Ak1w
pjgsBVoCgYEAxQLl9oU2/WRnSeG1aW7d008uTDp5v6VeWdpV9HKiK31RZQZbE/Ko
TKTNboaBEzY5+N0Btom0+kuZmz2gV4Bk64XTGtNTeA/r5XhmhJDEk1ypkJptzZQs
h3tHipOpl4c4S6x5j4CGkPhX5wwhGjcOMjHrWNeTL1bLf8NFXgusJK4CFQDeFtE0
/hOHcmGvGqWGEbvF8ikL6Q==
-----END DSA PRIVATE KEY-----'''
        dsa_public_key = (
            'AAAAB3NzaC1kc3MAAACBAPOoadq8pR33eIVyDZOHv3Jbz0xlGckGKF2Gj/Q+Rudp'
            'iSWPm1mgthWzWNMv8XABBx6uZGGvC48ECxq98b6aRCA8C16KtZJ8R37Nqae149VX'
            'nobAm1vzPCNeC6f+a+9242BDXbCvr/OeLwPTqgLewV85CBwBTAgA3s5/wkUa7msV'
            'AAAAFQD2XdRmh/57LQB9X48kfHVQxqsIZQAAAIBaGVv71nB62j/6DVEi/oCaI2a+'
            'YbOTNxcR0s3k/837DEPj/MtTWWNmjL5JiwI9A/oWn4l40r6YWKADq6I3MCLXhGwO'
            'JlkjATNUbv9N6kl8AyK7d9ytQ9cDYo9lezeG9L6fJokGpt86BxEJGqZrBgqqe3u1'
            'TKzIrfsCTXCmOCwFWgAAAIEAxQLl9oU2/WRnSeG1aW7d008uTDp5v6VeWdpV9HKi'
            'K31RZQZbE/KoTKTNboaBEzY5+N0Btom0+kuZmz2gV4Bk64XTGtNTeA/r5XhmhJDE'
            'k1ypkJptzZQsh3tHipOpl4c4S6x5j4CGkPhX5wwhGjcOMjHrWNeTL1bLf8NFXgus'
            'JK4='
        )

        credential = Credential.objects.create(user=self.user1,
                                               remote_user='remote_user')
        credential.private_key = rsa_private_key
        credential.save()
        self.assertEqual(credential.public_key, rsa_public_key)
        self.assertEqual(credential.key_type, 'ssh-rsa')

        credential = Credential.objects.create(user=self.user1,
                                               remote_user='remote_user')
        credential.private_key = dsa_private_key
        credential.save()
        self.assertEqual(credential.public_key, dsa_public_key)
        self.assertEqual(credential.key_type, 'ssh-dss')

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
