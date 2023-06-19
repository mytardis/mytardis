from django.urls import re_path

from tardis.apps.search.views import SearchView

urlpatterns = [
    re_path(r"^$", SearchView.as_view(), name="search"),
]
