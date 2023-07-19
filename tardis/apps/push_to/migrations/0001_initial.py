# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Credential',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key_type', models.CharField(max_length=25, null=True, verbose_name=b'Key type', blank=True)),
                ('public_key', models.TextField(null=True, verbose_name=b'Public key', blank=True)),
                ('private_key', models.TextField(null=True, verbose_name=b'Private key', blank=True)),
                ('remote_user', models.CharField(max_length=50, verbose_name=b'User name')),
                ('password', models.CharField(max_length=255, null=True, verbose_name=b'Password', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OAuthSSHCertSigningService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nickname', models.CharField(max_length=50, verbose_name=b'Nickname')),
                ('oauth_authorize_url', models.CharField(max_length=255, verbose_name=b'Authorize url')),
                ('oauth_token_url', models.CharField(max_length=255, verbose_name=b'Token url')),
                ('oauth_check_token_url', models.CharField(max_length=255, verbose_name=b'Check token url')),
                ('oauth_client_id', models.CharField(max_length=255, verbose_name=b'Client id')),
                ('oauth_client_secret', models.CharField(max_length=255, verbose_name=b'Client secret')),
                ('cert_signing_url', models.CharField(max_length=255, verbose_name=b'Cert signing url')),
                ('allow_for_all', models.BooleanField(default=False, verbose_name=b'Allow for all')),
                ('allowed_groups', models.ManyToManyField(to='auth.Group', blank=True)),
            ],
            options={
                'verbose_name': 'OAuth2 SSH cert signing service',
                'verbose_name_plural': 'OAuth2 SSH cert signing services',
            },
        ),
        migrations.CreateModel(
            name='RemoteHost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key_type', models.CharField(max_length=25, null=True, verbose_name=b'Key type', blank=True)),
                ('public_key', models.TextField(null=True, verbose_name=b'Public key', blank=True)),
                ('private_key', models.TextField(null=True, verbose_name=b'Private key', blank=True)),
                ('nickname', models.CharField(max_length=50, verbose_name=b'Nickname')),
                ('logo_img', models.CharField(max_length=255, null=True, verbose_name=b'Image url', blank=True)),
                ('host_name', models.CharField(max_length=50, verbose_name=b'Host name')),
                ('port', models.IntegerField(default=22, verbose_name=b'Port')),
                ('administrator', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='oauthsshcertsigningservice',
            name='allowed_remote_hosts',
            field=models.ManyToManyField(to='push_to.RemoteHost'),
        ),
        migrations.AddField(
            model_name='oauthsshcertsigningservice',
            name='allowed_users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='remote_hosts',
            field=models.ManyToManyField(to='push_to.RemoteHost'),
        ),
        migrations.AddField(
            model_name='credential',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
