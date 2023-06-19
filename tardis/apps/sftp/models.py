# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db import models


class SFTPPublicKey(models.Model):
    """Model for associated SFTP public keys with users

    :param user: user who owns this public key
    :type user: ForeignKey for User
    :param name: name for this public key
    :type name: string
    :param public_key: OpenSSH formatted public key
    :type public_key: string
    :param added: date the public key was added (Optional)
    :type added: date
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField('Device name', max_length=256)
    key_type = models.CharField("Key Type", max_length=100)
    public_key = models.TextField('Public Key')
    added = models.DateField("Added", auto_now_add=True)

    def __str__(self):
        return str(self.user) + ": " + self.name
