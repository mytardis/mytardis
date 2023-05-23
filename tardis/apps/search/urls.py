from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from tardis.apps.search.views import SearchView

urlpatterns = [
    url(r"^$", login_required(SearchView.as_view()), name="search"),
]
