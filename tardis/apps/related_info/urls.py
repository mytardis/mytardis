from django.conf.urls import url

from .views import index
from .views import list_or_create_related_info
from .views import get_or_update_or_delete_related_info


urlpatterns = [
    url(r'^(?P<experiment_id>\d+)/$', index,
        name='tardis.apps.related_info.views.index'),
    url(r'^experiment/(?P<experiment_id>\d+)/related-info/$',
        list_or_create_related_info,
        name='tardis.apps.related_info.views.list_or_create_related_info'),
    url(r'^experiment/(?P<experiment_id>\d+)/related-info/(?P<ps_id>\d+)$',
        get_or_update_or_delete_related_info,
        name='tardis.apps.related_info.views.get_or_update_or_delete_related_info'),
]
