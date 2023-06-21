# -*- coding: utf-8 -*-

from django.urls import re_path

from . import views

app_name = "tardis.apps.sftp"
urlpatterns = [
    re_path(
        r"^cyberduck/connection.png$",
        views.cybderduck_connection_window,
        name="cyberduck_connection_window",
    ),
    re_path(r"^$", views.sftp_access, name="index"),
    re_path(r"^keys/$", views.sftp_keys, name="sftp_keys"),
]
