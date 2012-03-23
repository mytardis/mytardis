from django.conf import settings

def single_search_processor(request):

    context = {}
    single_search_on = False
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

def registration_processor(request):
    def is_registration_enabled():
        try:
            if 'registration' in settings.INSTALLED_APPS:
                return True
        except AttributeError:
            pass
        return False
    return {'registration_enabled': is_registration_enabled()}
