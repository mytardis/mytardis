from django.conf.urls import url, include

from tardis.search.views import search_experiment

# from tardis.search.views import SingleSearchView,

urlpatterns = [
    # url(r'^\?$', SingleSearchView.as_view(), name='haystack_search'),
    url(r'', include('haystack.urls')),
    url(r'^experiment/$', search_experiment,
        name='tardis.search.views.search_experiment'),

]
