from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'tardis.apps.oaipmh.views.endpoint', name="oaipmh-endpoint"),
)