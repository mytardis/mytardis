from django.conf.urls import url

from .views import index
from .views import list_or_create_for_code
from .views import get_or_update_or_delete_for_code


urlpatterns = [
    url(r'^(?P<experiment_id>\d+)/$', index,
        name='tardis.apps.anzsrc_codes.views.index'),
    url(r'^experiment/(?P<experiment_id>\d+)/for-code/$',
        list_or_create_for_code,
        name='tardis.apps.anzsrc_codes.views.list_or_create_for_code'),
    url(r'^experiment/(?P<experiment_id>\d+)/for-code/(?P<ps_id>\d+)$',
        get_or_update_or_delete_for_code,
        name='tardis.apps.anzsrc_codes.views.get_or_update_or_delete_for_code')
]
