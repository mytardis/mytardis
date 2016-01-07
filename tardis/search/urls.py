from django.conf.urls import url

from tardis.search.views import SingleSearchView, retrieve_field_list, \
    search_experiment

urlpatterns = [
    url(r'^/?$', SingleSearchView.as_view(), name='haystack_search'),
    url(r'^parameter_field_list/$', retrieve_field_list,
        name='search_retrieve_field_list'),
    url(r'^datafile/$', 'tardis.search.views.search_datafile'),
    url(r'^experiment/$', search_experiment, name='search_experiment'),

]
