from django.urls import re_path

from .views import (
    get_or_update_or_delete_related_info,
    index,
    list_or_create_related_info,
)

urlpatterns = [
    re_path(
        r"^(?P<experiment_id>\d+)/$", index, name="tardis.apps.related_info.views.index"
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/related-info/$",
        list_or_create_related_info,
        name="tardis.apps.related_info.views.list_or_create_related_info",
    ),
    re_path(
        r"^experiment/(?P<experiment_id>\d+)/related-info/(?P<ps_id>\d+)$",
        get_or_update_or_delete_related_info,
        name="tardis.apps.related_info.views.get_or_update_or_delete_related_info",
    ),
]
