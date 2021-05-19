import base64

from io import StringIO

from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from paramiko import RSAKey, SSHClient, MissingHostKeyPolicy, \
    AutoAddPolicy, PKey, DSSKey, ECDSAKey, PublicBlob
from paramiko.config import SSH_PORT

from tardis.tardis_portal.models import DataFile

from .apps import PushToConfig
from .exceptions import NoSuitableCredential


class KeyPair(models.Model):
    """
    A key pair
    """

    key_type = models.CharField('Key type',
                                max_length=100,
                                blank=True,
                                null=True)
    public_key = models.TextField('Public key',
                                  blank=True,
                                  null=True)
    private_key = models.TextField('Private key', blank=True, null=True)

    class Meta:
        abstract = True

    # pylint: disable=W0222
    def save(self, *args, **kwargs):

        # Attempt to auto-complete the public key & key type if missing
        if not self.key_type and not self.public_key and self.private_key:
            # Attempt to guess the key type from private key:
            if self.private_key.startswith('-----BEGIN RSA PRIVATE KEY-----'):
                self.key_type = 'ssh-rsa'
            elif self.private_key.startswith(
                    '-----BEGIN DSA PRIVATE KEY-----'):
                self.key_type = 'ssh-dss'
                # TODO: work out what to do with EC keys
        if self.key_type and self.private_key and not self.public_key:
            self.public_key = self.key.get_base64()

        super().save(*args, **kwargs)

    @property
    def key(self):
        """
        :return: a subclass of PKey of the appropriate key type
        :rtype: PKey
        :raises ValidationError:
        """

        # Check if the key pair exists: at least a public or private part of
        # the key is required, as well as the key type.
        if not self.key_type:
            return None
        if not self.public_key and not self.private_key:
            return None

        public_key = None
        private_key = None
        if self.public_key:
            public_key = base64.b64decode(self.public_key)
        if self.private_key:
            private_key = StringIO(self.private_key)

        if self.key_type == 'ssh-dss':
            pkey = DSSKey(data=public_key, file_obj=private_key)
        elif self.key_type == 'ssh-rsa':
            pkey = RSAKey(data=public_key, file_obj=private_key)
        elif self.key_type.startswith('ecdsa'):
            pkey = ECDSAKey(data=public_key, file_obj=private_key)
        elif self.key_type == 'ssh-rsa-cert-v01@openssh.com':
            pkey = RSAKey(data=public_key, file_obj=private_key)
            pkey.public_blob = PublicBlob(self.key_type, public_key)
        else:
            raise ValidationError('Unsupported key type: ' + self.key_type)

        return pkey

    @key.setter
    def key(self, pkey):
        """
        Creates a new Key object created from a paramiko pkey object
        :param pkey: Public Key
        :type pkey: PKey
        :raises ValueError:
        """
        if not isinstance(pkey, PKey):
            raise ValueError('invalid PKey object supplied')
        if pkey.public_blob is not None:
            self.key_type = pkey.public_blob.key_type
            self.public_key = base64.b64encode(pkey.public_blob.key_blob).decode()
        else:
            self.key_type = pkey.get_name()
            self.public_key = pkey.get_base64()
        self.private_key = None
        if pkey.can_sign():
            key_data = StringIO()
            pkey.write_private_key(key_data)
            self.private_key = key_data.getvalue()


class RemoteHost(KeyPair):
    """
    A remote host that may be connected to via SSH
    """
    administrator = models.ForeignKey(User, on_delete=models.CASCADE)
    nickname = models.CharField(
        'Nickname',
        max_length=50,
        blank=False,
        null=False)
    logo_img = models.CharField(
        'Image url',
        max_length=255,
        blank=True,
        null=True)
    host_name = models.CharField('Host name', max_length=50)
    port = models.IntegerField('Port', default=SSH_PORT)

    def __str__(self):
        return self.nickname + ' | ' + self.host_name + ':' + str(self.port)


class OAuthSSHCertSigningService(models.Model):
    """
    Connection parameters for an OAuth2 SSH certificate signing service.
    Supports certificate signing server available here:
    https://github.com/monash-merc/ssh-authz
    """
    nickname = models.CharField('Nickname', max_length=50)
    oauth_authorize_url = models.CharField('Authorize url', max_length=255)
    oauth_token_url = models.CharField('Token url', max_length=255)
    oauth_check_token_url = models.CharField('Check token url', max_length=255)
    oauth_client_id = models.CharField('Client id', max_length=255)
    oauth_client_secret = models.CharField('Client secret', max_length=255)
    cert_signing_url = models.CharField('Cert signing url', max_length=255)
    allowed_remote_hosts = models.ManyToManyField(RemoteHost)
    allowed_groups = models.ManyToManyField(Group, blank=True)
    allowed_users = models.ManyToManyField(User, blank=True)
    allow_for_all = models.BooleanField('Allow for all', default=False)

    class Meta:
        verbose_name = 'OAuth2 SSH cert signing service'
        verbose_name_plural = 'OAuth2 SSH cert signing services'

    def __str__(self):
        return self.nickname

    @staticmethod
    def get_available_signing_services(user):
        """
        Gets all SSH cert signing services available for a given user
        :param User user: User
        :return: allowed signing services
        :rtype: User
        """
        return (
            OAuthSSHCertSigningService.objects.filter(
                allowed_users=user) |
            OAuthSSHCertSigningService.objects.filter(
                allowed_groups__user=user) |
            OAuthSSHCertSigningService.objects.filter(
                allow_for_all=True)).distinct()

    @staticmethod
    def get_oauth_service(user, service_id):
        """
        @type user: User
        @type service_id: int
        """
        return (OAuthSSHCertSigningService.objects.filter(
            allowed_users=user,
            pk=service_id) |
                OAuthSSHCertSigningService.objects.filter(
                    allow_for_all=True,
                    pk=service_id)).first()


class DBHostKeyPolicy(MissingHostKeyPolicy):
    """
    Host key verification policy based on the host key stored in the database.
    """

    def missing_host_key(self, client, hostname, key):
        """
        @type key: PKey
        """
        acceptable_key_fingerprint = RemoteHost.objects.get(
            host_name=hostname).key.get_fingerprint()
        host_key_fingerprint = key.get_fingerprint()
        if acceptable_key_fingerprint != host_key_fingerprint:
            raise Exception(
                'Host key for host %s not accepted' % hostname)


class Credential(KeyPair):
    """
    A credential that may contain a password and/or key. The auth method chosen
    depends on the credentials available, allowed auth methods, and priorities
    defined by the SSH client.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    remote_hosts = models.ManyToManyField(RemoteHost)
    remote_user = models.CharField('User name', max_length=50)
    password = models.CharField(
        'Password',
        max_length=255,
        blank=True,
        null=True)

    def _hostname_list(self):
        return [h.host_name for h in self.remote_hosts.all()]

    def __str__(self):
        hosts = str.join(', ', self._hostname_list())
        return self.user.username + ' | ' + \
               self.remote_user + ' (' + hosts + ')'

    @staticmethod
    def get_suitable_credential(tardis_user, remote_host, remote_user=None):
        existing_credentials = Credential.objects.filter(
            user=tardis_user,
            remote_hosts=remote_host)
        if remote_user is not None:
            existing_credentials = existing_credentials.filter(
                remote_user=remote_user)

        for credential in existing_credentials:
            if credential.verify_remote_access(remote_host):
                return credential

        raise NoSuitableCredential()

    @staticmethod
    def generate_keypair_credential(
            tardis_user, remote_user, remote_hosts,
            bit_length=2048):
        """
        Generates and saves an RSA key pair credential. Credentials returned
        by this method are intended to be registered on remote systems before
        being used.
        @type tardis_user: User
        @type remote_user: str
        @type bit_length: int
        @type remote_hosts: list[RemoteHost]
        :return: the generated credential
        :rtype: object
        """
        key = RSAKey.generate(bits=bit_length)
        credential = Credential(user=tardis_user, remote_user=remote_user)
        credential.key = key
        credential.save()

        if remote_hosts is not None:
            credential.remote_hosts.add(*remote_hosts)
            credential.save()

        return credential

    def get_client_for_host(self, remote_host):
        """
        Attempts to establish a connection with the remote_host using this
        credential object. The remote_host may be any host, but only those in
        the remote_hosts field are expected to work.
        @type remote_host: .RemoteHost
        :return: a connected SSH client
        :rtype: SSHClient
        """
        ssh = SSHClient()

        # Decide whether to verify the host key
        if remote_host.key is not None:
            ssh.set_missing_host_key_policy(DBHostKeyPolicy())
        else:
            ssh.set_missing_host_key_policy(AutoAddPolicy())

        ssh.connect(hostname=remote_host.host_name,
                    port=remote_host.port,
                    username=self.remote_user,
                    password=self.password,
                    pkey=self.key)

        return ssh

    def verify_remote_access(self, remote_host=None):
        """
        @type remote_host: RemoteHost
        """
        if remote_host is not None:
            remote_hosts = [remote_host]
        else:
            remote_hosts = self.remote_hosts.all()

        for host in remote_hosts:
            try:
                self.get_client_for_host(host)
            except Exception:
                return False
        return True


class Request(models.Model):
    """
    PushTo request
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(null=False, default=timezone.now)
    object_type = models.CharField(max_length=10, null=False)
    object_id = models.PositiveIntegerField(null=False)
    credential = models.ForeignKey(Credential, on_delete=models.CASCADE)
    host = models.ForeignKey(RemoteHost, on_delete=models.CASCADE)
    base_dir = models.CharField(max_length=100, null=True)
    message = models.CharField(max_length=100, null=True)


class Progress(models.Model):
    """
    Files copy progress
    """
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    datafile = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    status = models.PositiveIntegerField(null=False, default=0)
    message = models.CharField(max_length=100, null=True)
    retry = models.PositiveIntegerField(null=False, default=0)
    timestamp = models.DateTimeField(null=True)


class RemoteHostAdmin(admin.ModelAdmin):
    """
    Hides the private key field, which is not necessary for host keys
    """
    fields = ['nickname', 'administrator', 'host_name', 'port', 'key_type',
              'public_key', 'logo_img']


class CredentialForm(forms.ModelForm):
    class Meta:
        fields = '__all__'
        model = Credential
        widgets = {'password': forms.PasswordInput()}


class CredentialAdmin(admin.ModelAdmin):
    form = CredentialForm


# Register the models with the admin
if apps.is_installed(PushToConfig.name):
    admin.site.register(RemoteHost, RemoteHostAdmin)
    admin.site.register(Credential, CredentialAdmin)
    admin.site.register(OAuthSSHCertSigningService)
