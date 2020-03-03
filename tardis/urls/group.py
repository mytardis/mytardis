'''
Group URLs
'''
from django.conf.urls import url

from tardis.tardis_portal.views import (
    retrieve_group_userlist,
    retrieve_group_userlist_readonly,
    add_user_to_group,
    remove_user_from_group,
    manage_groups
)

group_urls = [
    url(r'^groups/$', manage_groups,
        name='tardis.tardis_portal.views.manage_groups'),
    url(r'^(?P<group_id>\d+)/$', retrieve_group_userlist,
        name='tardis.tardis_portal.views.retrieve_group_userlist'),
    url(r'^(?P<group_id>\d+)/readonly$', retrieve_group_userlist_readonly,
        name='tardis.tardis_portal.views.retrieve_group_userlist_readonly'),
    url(r'^(?P<group_id>\d+)/add/(?P<username>[\w.@+-]+)/$',
        add_user_to_group,
        name='tardis.tardis_portal.views.add_user_to_group'),
    url(r'^(?P<group_id>\d+)/remove/(?P<username>[\w.@+-]+)/$',
        remove_user_from_group,
        name='tardis.tardis_portal.views.remove_user_from_group'),
]
