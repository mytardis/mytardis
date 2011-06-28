from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'^$','tardis.apps.hpctardis.views.test'),
    )
    