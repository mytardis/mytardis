# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

app_name = "tardis.apps.sftp"
urlpatterns = [
    url(r'^cyberduck/connection.png$',
         views.cybderduck_connection_window,
         name='cyberduck_connection_window'),
    url(r'^$', views.sftp_access, name='index'),
    url(r'^keys/$', views.sftp_keys, name='sftp_keys'),
]
