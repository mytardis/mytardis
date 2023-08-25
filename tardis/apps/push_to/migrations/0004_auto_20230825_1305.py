# Generated by Django 3.2.7 on 2023-08-25 03:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('push_to', '0003_auto_20210216_1322'),
    ]

    operations = [
        migrations.AlterField(
            model_name='credential',
            name='key_type',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Key type'),
        ),
        migrations.AlterField(
            model_name='credential',
            name='password',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Password'),
        ),
        migrations.AlterField(
            model_name='credential',
            name='private_key',
            field=models.TextField(blank=True, null=True, verbose_name='Private key'),
        ),
        migrations.AlterField(
            model_name='credential',
            name='public_key',
            field=models.TextField(blank=True, null=True, verbose_name='Public key'),
        ),
        migrations.AlterField(
            model_name='credential',
            name='remote_user',
            field=models.CharField(max_length=50, verbose_name='User name'),
        ),
        migrations.AlterField(
            model_name='oauthsshcertsigningservice',
            name='allow_for_all',
            field=models.BooleanField(default=False, verbose_name='Allow for all'),
        ),
        migrations.AlterField(
            model_name='oauthsshcertsigningservice',
            name='cert_signing_url',
            field=models.CharField(max_length=255, verbose_name='Cert signing url'),
        ),
        migrations.AlterField(
            model_name='oauthsshcertsigningservice',
            name='nickname',
            field=models.CharField(max_length=50, verbose_name='Nickname'),
        ),
        migrations.AlterField(
            model_name='oauthsshcertsigningservice',
            name='oauth_authorize_url',
            field=models.CharField(max_length=255, verbose_name='Authorize url'),
        ),
        migrations.AlterField(
            model_name='oauthsshcertsigningservice',
            name='oauth_check_token_url',
            field=models.CharField(max_length=255, verbose_name='Check token url'),
        ),
        migrations.AlterField(
            model_name='oauthsshcertsigningservice',
            name='oauth_client_id',
            field=models.CharField(max_length=255, verbose_name='Client id'),
        ),
        migrations.AlterField(
            model_name='oauthsshcertsigningservice',
            name='oauth_client_secret',
            field=models.CharField(max_length=255, verbose_name='Client secret'),
        ),
        migrations.AlterField(
            model_name='oauthsshcertsigningservice',
            name='oauth_token_url',
            field=models.CharField(max_length=255, verbose_name='Token url'),
        ),
        migrations.AlterField(
            model_name='remotehost',
            name='host_name',
            field=models.CharField(max_length=50, verbose_name='Host name'),
        ),
        migrations.AlterField(
            model_name='remotehost',
            name='key_type',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Key type'),
        ),
        migrations.AlterField(
            model_name='remotehost',
            name='logo_img',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Image url'),
        ),
        migrations.AlterField(
            model_name='remotehost',
            name='nickname',
            field=models.CharField(max_length=50, verbose_name='Nickname'),
        ),
        migrations.AlterField(
            model_name='remotehost',
            name='port',
            field=models.IntegerField(default=22, verbose_name='Port'),
        ),
        migrations.AlterField(
            model_name='remotehost',
            name='private_key',
            field=models.TextField(blank=True, null=True, verbose_name='Private key'),
        ),
        migrations.AlterField(
            model_name='remotehost',
            name='public_key',
            field=models.TextField(blank=True, null=True, verbose_name='Public key'),
        ),
    ]
