from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
                       (r'^$', 'tardis.apps.oaipmh.views.endpoint'),)