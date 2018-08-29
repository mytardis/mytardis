from django.conf.urls import url, include

from tardis.search.views import (
    retrieve_field_list,
    search_experiment
)

# from tardis.search.views import SingleSearchView,

urlpatterns = [
    # url(r'^\?$', SingleSearchView.as_view(), name='haystack_search'),
    url(r'', include('haystack.urls')),
    url(r'^parameter_field_list/$', retrieve_field_list,
        name='search_retrieve_field_list'),
    url(r'^experiment/$', search_experiment,
        name='tardis.search.views.search_experiment'),

]
