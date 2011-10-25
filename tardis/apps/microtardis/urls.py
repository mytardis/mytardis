from django.conf.urls.defaults import patterns
from tardis.urls import urlpatterns as tardisurls

urlpatterns = patterns('tardis.apps.microtardis.views',
    (r'^$', 'index_microtardis'),
    (r'^about/$', 'about_microtardis'),
)

urlpatterns += tardisurls
