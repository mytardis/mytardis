# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^cyberduck/connection.png$',
         views.cybderduck_connection_window,
         name='cyberduck_connection_window'),
    url(r'^$', views.sftp_access, name='index'),
]
