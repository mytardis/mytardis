from StringIO import StringIO
import base64

from django.contrib import admin
from django.core.exceptions import ValidationError
from paramiko import RSAKey, RSACert, SSHClient, MissingHostKeyPolicy, AutoAddPolicy, PKey, DSSKey, ECDSAKey
from django.db import models, transaction
from django.contrib.auth.models import User, Group
from paramiko.config import SSH_PORT
from tardis.apps.push_to.exceptions import NoSuitableCredential


class KeyField(models.TextField):

    """
    A key pair
    """

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return KeyField._to_pkey(value)

    def to_python(self, value):
        if isinstance(value, PKey):
            return value

        return KeyField._to_pkey(value)

    def get_prep_value(self, value):
        if isinstance(value, PKey):
            return KeyField._from_pkey(value)
        return None

    def value_from_object(self, obj):
        value = super(KeyField, self).value_from_object(obj)
        return self.get_prep_value(value)

    def clean(self, value, model_instance):
        value = self.to_python(value)
        return value

    @staticmethod
    def _to_pkey(value):
        """
        :return: a subclass of PKey of the appropriate key type
        """
        try:
            key_type, public_key, private_key = value.split('.')
        except ValueError:
            raise ValidationError('Malformed key data')
        key_type = base64.b64decode(key_type)
        public_key = base64.b64decode(public_key)
        private_key = StringIO(private_key)
        if key_type == 'ssh-dss':
            pkey = DSSKey(data=public_key, file_obj=private_key)
        elif key_type == 'ssh-rsa':
            pkey = RSAKey(data=public_key, file_obj=private_key)
        elif key_type == 'ecdsa-sha2-nistp256':
            pkey = ECDSAKey(data=public_key, file_obj=private_key)
        elif key_type == 'ssh-rsa-cert-v01@openssh.com':
            pkey = RSACert(data=public_key, privkey_file_obj=private_key)
        else:
            raise ValidationError('Unsupported key type')

        return pkey

    @staticmethod
    def _from_pkey(pkey):
        """
        Creates a new Key object created from a paramiko pkey object
        @type pkey: PKey
        :return: the Key object that has been saved
        """
        key_type = base64.b64encode(pkey.get_name())
        public_key = pkey.get_base64()
        private_key = ''
        if pkey.can_sign():
            key_data = StringIO()
            pkey.write_private_key(key_data)
            private_key = key_data.getvalue()

        key = key_type + '.' + public_key + '.' + private_key

        return key


class RemoteHost(models.Model):

    """
    A remote host that may be connected to via SSH
    """
    administrator = models.ForeignKey(User)
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
    host_key = KeyField(blank=True, null=True)

    def __unicode__(self):
        return self.nickname + ' | ' + self.host_name + ':' + str(self.port)


class OAuthSSHCertSigningService(models.Model):
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

    def __unicode__(self):
        return self.nickname

    @staticmethod
    def get_available_signing_services(user):
        """
        Gets all SSH cert signing services available for a given user
        @type: user: User
        :return: allowed signing services
        """
        return (
            OAuthSSHCertSigningService.objects.filter(
                allowed_users=user) | OAuthSSHCertSigningService.objects.filter(
                allowed_groups__user=user) | OAuthSSHCertSigningService.objects.filter(
                allow_for_all=True)).distinct()

    @staticmethod
    def get_oauth_service(user, service_id):
        """
        @type user: User
        @type service_id: int
        """
        return OAuthSSHCertSigningService.objects.get(
            allowed_users=user,
            pk=service_id)


class DBHostKeyPolicy(MissingHostKeyPolicy):

    """
    Host key verification policy based on the host key stored in the database.
    """

    def missing_host_key(self, client, hostname, key):
        """
        @type key: PKey
        """
        acceptable_key_fingerprint = RemoteHost.objects.get(
            host_name=hostname).host_key.get_fingerprint()
        host_key_fingerprint = key.get_fingerprint()
        if acceptable_key_fingerprint != host_key_fingerprint:
            raise Exception(
                'Host key for host %s not accepted: expected %s, got %s' %
                (hostname, acceptable_key_fingerprint, host_key_fingerprint))


class Credential(models.Model):

    """
    A credential that may contain a password and/or key. The auth method chosen depends on the credentials available,
    allowed auth methods, and priorities defined by the SSH client.
    """
    user = models.ForeignKey(User)
    remote_hosts = models.ManyToManyField(RemoteHost)
    remote_user = models.CharField('User name', max_length=50)
    password = models.CharField(
        'Password',
        max_length=255,
        blank=True,
        null=True)
    key = KeyField(blank=True, null=True)

    def _hostname_list(self):
        return [h.host_name for h in self.remote_hosts.all()]

    def __unicode__(self):
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
            tardis_user,
            remote_user,
            remote_hosts,
            bit_length=2048):
        """
        Generates and saves an RSA key pair credential. Credentials returned by this method are intended to be
        registered on remote systems before being used.
        @type tardis_user: User
        @type remote_user: str
        @type bit_length: int
        @type remote_hosts: list[RemoteHost]
        :return: the generated credential
        """

        with transaction.atomic():
            key = RSAKey.generate(bits=bit_length)
            credential = Credential(
                user=tardis_user,
                remote_user=remote_user,
                key=key)
            credential.save()

            if remote_hosts is not None:
                credential.remote_hosts.add(*remote_hosts)
                credential.save()

            return credential

    def get_client_for_host(self, remote_host):
        """
        Attempts to establish a connection with the remote_host using this credential object.
        The remote_host may be any host, but only those in the remote_hosts field are expected to work.
        @type remote_host: .RemoteHost
        :return: a connected SSH client
        """
        ssh = SSHClient()

        # Decide whether to verify the host key
        if remote_host.host_key is not None:
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

# Register the models with the admin
admin.site.register(RemoteHost)
admin.site.register(Credential)
admin.site.register(OAuthSSHCertSigningService)
