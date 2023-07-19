"""
Group URLs
"""
from django.urls import re_path

from tardis.tardis_portal.views import (
    add_user_to_group,
    manage_groups,
    remove_user_from_group,
    retrieve_group_userlist,
    retrieve_group_userlist_readonly,
)

group_urls = [
    re_path(
        r"^groups/$", manage_groups, name="tardis.tardis_portal.views.manage_groups"
    ),
    re_path(
        r"^(?P<group_id>\d+)/$",
        retrieve_group_userlist,
        name="tardis.tardis_portal.views.retrieve_group_userlist",
    ),
    re_path(
        r"^(?P<group_id>\d+)/readonly$",
        retrieve_group_userlist_readonly,
        name="tardis.tardis_portal.views.retrieve_group_userlist_readonly",
    ),
    re_path(
        r"^(?P<group_id>\d+)/add/(?P<username>[\w.@+-]+)/$",
        add_user_to_group,
        name="tardis.tardis_portal.views.add_user_to_group",
    ),
    re_path(
        r"^(?P<group_id>\d+)/remove/(?P<username>[\w.@+-]+)/$",
        remove_user_from_group,
        name="tardis.tardis_portal.views.remove_user_from_group",
    ),
]
