from django.conf.urls import patterns

urlpatterns = patterns(
    'tardis.apps.synch_linking',
    (r'^url-by-id/(?P<mongodb_id>\w+)/$', 'views.url_by_id'),
)
