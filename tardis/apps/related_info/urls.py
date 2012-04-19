from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('tardis.apps.related_info.views',
    url(r'^(?P<experiment_id>\d+)/$', 'index'),
    url(r'^experiment/(?P<experiment_id>\d+)/related-info/$',
        'list_related_info'),
    url(r'^experiment/(?P<experiment_id>\d+)/related-info/(?P<related_info_id>\d+)$',
        'get_related_info'),
)
