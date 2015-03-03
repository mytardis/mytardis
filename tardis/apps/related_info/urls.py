from django.conf.urls import patterns, url

urlpatterns = patterns('tardis.apps.related_info.views',
    url(r'^(?P<experiment_id>\d+)/$', 'index'),
    url(r'^experiment/(?P<experiment_id>\d+)/related-info/$',
        'list_or_create_related_info'),
    url(r'^experiment/(?P<experiment_id>\d+)/related-info/(?P<ps_id>\d+)$',
        'get_or_update_or_delete_related_info'),
)
