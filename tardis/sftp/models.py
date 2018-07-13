# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User

from paramiko.rsakey import RSAKey


class SFTPPublicKey(models.Model):
    """Model for associated SFTP public keys with users

    :param user: user who owns this public key
    :type user: ForeignKey for User
    :param public_key: Public key
    :type public_key: string
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField('Device name', max_length=256)
    key_type = models.CharField("Key Type", max_length=100)
    public_key = models.TextField('Public Key')
    added = models.DateField("Added", auto_now_add=True)

    def __str__(self):
        return str(self.user) + ": " + self.name
