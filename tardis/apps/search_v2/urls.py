from django.conf.urls import url

from tardis.apps.search_v2.views import SearchV2View, search_experiment

urlpatterns = [
    url(r'^\?$', SearchV2View.as_view(), name='search_v2'),
    url(r'^experiment/$', search_experiment,
        name='tardis.search.views.search_experiment'),

]
