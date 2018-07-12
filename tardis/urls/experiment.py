'''
URLs for experiments
'''
from django.conf.urls import url

from tardis.tardis_portal.views import ExperimentView

from tardis.tardis_portal.views import (
    edit_experiment,
    create_experiment,
    add_experiment_access_user,
    remove_experiment_access_user,
    change_user_permissions,
    retrieve_access_list_user,
    retrieve_access_list_user_readonly,
    add_experiment_access_group,
    remove_experiment_access_group,
    change_group_permissions,
    retrieve_access_list_group,
    retrieve_access_list_group_readonly,
    create_user,
    create_group,
    retrieve_access_list_external,
    retrieve_access_list_tokens,
    control_panel,
    create_token,
    view_rifcs,
    experiment_public_access_badge,
    add_dataset
)

user_pattern = '[\w\-][\w\-\.]+(@[\w\-][\w\-\.]+[a-zA-Z]{1,4})*'

experiment_urls = [
    url(r'^view/(?P<experiment_id>\d+)/$', ExperimentView.as_view(),
        name='tardis_portal.view_experiment'),
    url(r'^edit/(?P<experiment_id>\d+)/$', edit_experiment,
        name='tardis.tardis_portal.views.edit_experiment'),
    url(r'^create/$', create_experiment,
        name='tardis.tardis_portal.views.create_experiment'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/add/user/'
        '(?P<username>%s)/$' % user_pattern,
        add_experiment_access_user,
        name='tardis.tardis_portal.views.add_experiment_access_user'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/remove/user/'
        '(?P<username>%s)/$' % user_pattern, remove_experiment_access_user,
        name='tardis.tardis_portal.views.remove_experiment_access_user'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/change/user/'
        '(?P<username>%s)/$' % user_pattern, change_user_permissions,
        name='tardis.tardis_portal.views.change_user_permissions'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/user/$',
        retrieve_access_list_user,
        name='tardis.tardis_portal.views.retrieve_access_list_user'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/user/readonly/$',
        retrieve_access_list_user_readonly,
        name='tardis.tardis_portal.views.retrieve_access_list_user_readonly'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/add/group/'
        '(?P<groupname>.+)/$', add_experiment_access_group,
        name='tardis.tardis_portal.views.add_experiment_access_group'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/remove/group/'
        '(?P<group_id>\d+)/$', remove_experiment_access_group,
        name='tardis.tardis_portal.views.remove_experiment_access_group'),
    url(r'^control_panel/create/group/$', create_group,
        name='tardis.tardis_portal.views.create_group'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/change/group/'
        '(?P<group_id>\d+)/$', change_group_permissions,
        name='tardis.tardis_portal.views.change_group_permissions'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/group/$',
        retrieve_access_list_group,
        name='tardis.tardis_portal.views.retrieve_access_list_group'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/group/readonly/$',
        retrieve_access_list_group_readonly,
        name='tardis.tardis_portal.views.retrieve_access_list_group_readonly'),
    url(r'^control_panel/create/user/$', create_user,
        name='tardis.tardis_portal.views.create_user'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/external/$',
        retrieve_access_list_external,
        name='tardis.tardis_portal.views.retrieve_access_list_external'),
    url(r'^control_panel/(?P<experiment_id>\d+)/access_list/tokens/$',
        retrieve_access_list_tokens,
        name='tardis.tardis_portal.views.retrieve_access_list_tokens'),
    url(r'^control_panel/$', control_panel,
        name='tardis.tardis_portal.views.control_panel'),
    url(r'^view/(?P<experiment_id>\d+)/create_token/$', create_token,
        name='tardis.tardis_portal.views.create_token'),
    url(r'^view/(?P<experiment_id>\d+)/rifcs/$', view_rifcs,
        name='tardis.tardis_portal.views.control_panel.view_rifcs'),
    url(r'^view/(?P<experiment_id>\d+)/public_access_badge/$',
        experiment_public_access_badge,
        name='tardis.tardis_portal.views.control_panel.experiment_public_access_badge'),
    url(r'^(?P<experiment_id>\d+)/add-dataset$', add_dataset,
        name='tardis.tardis_portal.views.add_dataset'),
]
