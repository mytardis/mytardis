from django.conf.urls.defaults import patterns

urlpatterns = patterns('tardis.apps.hpctardis.views',
    (r'^$','test'),
    (r'^protocol/$','protocol'),
    (r'^login/$','login'),
    (r'^addfiles/$','addfiles')
    )
    