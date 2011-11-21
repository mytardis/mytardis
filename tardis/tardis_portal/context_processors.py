from tardis.tardis_portal.forms import RawSearchForm
from django.conf import settings

def single_search_processor(request):

    context = {}
    form = None
    query = ''
    try:
        if settings.SINGLE_SEARCH_ENABLED: 	
            form = RawSearchForm() 
            if form.is_valid():
                query = form.cleaned_data['q'] 
    except AttributeError:
        pass

    context =  {
	    'search_form': form,
        'search_query': query,
    }

    return context

def tokenuser_processor(request):
    is_token_user = request.user.username == settings.TOKEN_USERNAME
    return {'is_token_user': is_token_user}
