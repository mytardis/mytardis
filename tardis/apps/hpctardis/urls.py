from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'^$','tardis.apps.hpctardis.views.test'),
    (r'^publisher/(?P<experiment_id>\d+)/$','tardis.apps.hpctardis.views.publish_experiment'),
    (r'^rif_cs/$','tardis.apps.hpctardis.views.rif_cs')
    )
    