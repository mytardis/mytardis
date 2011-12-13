from django.conf import settings

def single_search_processor(request):

    context = {}
    single_search_on = True
    try:
        if settings.SINGLE_SEARCH_ENABLED: 	
            single_search_on = True
    except AttributeError:
        pass

    context =  {
	    'search_form': single_search_on,
    }

    return context

def tokenuser_processor(request):
    is_token_user = request.user.username == settings.TOKEN_USERNAME
    return {'is_token_user': is_token_user}
