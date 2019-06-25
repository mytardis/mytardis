from django.conf.urls import url

from tardis.apps.search.views import SearchView

urlpatterns = [
    url(r'^\?$', SearchView.as_view(), name='search'),
]
