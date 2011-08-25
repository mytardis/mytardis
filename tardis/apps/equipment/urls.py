from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
                       (r'^$', 'tardis.apps.equipment.views.index'),
                       (r'^search/$', 'tardis.apps.equipment.views.search'),
                       (r'^(?P<object_id>\d+)/$',
                        'tardis.apps.equipment.views.view_id'),
                       (r'^(?P<object_key>\w+)/$',
                        'tardis.apps.equipment.views.view_key'),
                       )
