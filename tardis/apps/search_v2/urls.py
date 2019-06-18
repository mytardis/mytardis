from django.conf.urls import url

from tardis.apps.search_v2.views import SearchV2View

urlpatterns = [
    url(r'^\?$', SearchV2View.as_view(), name='search_v2'),
]
