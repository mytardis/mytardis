from django.conf.urls import url

from .views import (
    index,
    search,
    view_id,
    view_key
)

urlpatterns = [
   url(r'^$', index, name='tardis.apps.equipment.views.index'),
   url(r'^search/$', search, name='tardis.apps.equipment.views.search'),
   url(r'^(?P<object_id>\d+)/$',
       view_id, name='tardis.apps.equipment.views.view_id'),
   url(r'^(?P<object_key>\w+)/$',
       view_key, name='tardis.apps.equipment.views.view_key'),
]
