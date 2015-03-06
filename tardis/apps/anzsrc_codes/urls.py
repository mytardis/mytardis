from django.conf.urls import patterns, url

urlpatterns = patterns('tardis.apps.anzsrc_codes.views',
    url(r'^(?P<experiment_id>\d+)/$', 'index'),
    url(r'^experiment/(?P<experiment_id>\d+)/for-code/$',
        'list_or_create_for_code'),
    url(r'^experiment/(?P<experiment_id>\d+)/for-code/(?P<ps_id>\d+)$',
        'get_or_update_or_delete_for_code'),

)
