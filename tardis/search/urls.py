from django.conf.urls import url

from tardis.search.views import SingleSearchView

urlpatterns = [
    url(r'^\?$', SingleSearchView.as_view(), name='haystack_search'),
]
