from tardis.tardis_portal.views import ExperimentSearchView
from tardis.tardis_portal.forms import RawSearchForm
from haystack.query import SearchQuerySet
from django.conf import settings

def single_search_processor(request):

    context = {}

    if settings.SINGLE_SEARCH_ENABLED: 
        sqs = SearchQuerySet()
	
	form = RawSearchForm() 

	q = ''
	if form.is_valid():
		q = form.cleaned_data['q']
	
        context =  {
		'search_form': form,
                'search_query': form.cleaned_data['q'] if form.is_valid() else '',
                }

    return context

def tokenuser_processor(request):
    is_token_user = request.user.username == settings.TOKEN_USERNAME
    return {'is_token_user': is_token_user}
