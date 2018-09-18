from django.conf.urls import url

from tardis.search.views import SingleSearchView, search_experiment

urlpatterns = [
    url(r'^\?$', SingleSearchView.as_view(), name='haystack_search'),
    url(r'^experiment/$', search_experiment,
        name='tardis.search.views.search_experiment'),

]
