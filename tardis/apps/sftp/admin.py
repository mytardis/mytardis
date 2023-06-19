# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import SFTPPublicKey

# Register SFTPPublicKey model in admin site
admin.site.register(SFTPPublicKey)
