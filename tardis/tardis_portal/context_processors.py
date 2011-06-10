from tardis.tardis_portal.views import ExperimentSearchView
from tardis.tardis_portal.forms import RawSearchForm
from haystack.query import SearchQuerySet
from django.conf import settings

def single_search_processor(request):

    context = {}

    if settings.SINGLE_SEARCH_ENABLED: 
        sqs = SearchQuerySet()

        search_view = ExperimentSearchView(
                template = "search/search.html",
                searchqueryset = sqs,
                form_class = RawSearchForm,
                )
        search_view.request = request
        search_view.form = search_view.build_form()
        search_view.query = search_view.get_query()

        (paginator, page) = search_view.build_page()

        context =  {'form': search_view.form,
                #'results': search_view.get_results(),
                'query': search_view.query,
                'page' : page,
                'paginator' : paginator 
                }
        context.update(search_view.extra_context())

    return context
