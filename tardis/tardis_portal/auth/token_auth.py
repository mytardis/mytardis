"""
token authentication module
"""
from ..models import Token
from ..auth.interfaces import GroupProvider

TOKEN_EXPERIMENT = '_token_experiment'


class TokenGroupProvider(GroupProvider):
    '''
    Transforms tokens into auth groups
    '''
    name = u'token_group'

    def getGroups(self, user):
        if hasattr(user, 'allowed_tokens'):
            tokens = Token.objects.filter(
                token__in=user.allowed_tokens)
            valid_tokens = []
            for token in tokens:
                if not token.is_expired():
                    valid_tokens.append(token)
            return valid_tokens
        return []

    def searchGroups(self, **kwargs):
        """
            return nothing because these are not groups in
            the standard sense
        """
        return []


class TokenAuthMiddleware(object):
    '''
    adds tokens to the user object and the session from a GET query
    '''
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        return response

    def process_request(self, request):
        all_tokens_set = set()
        all_tokens_set.add(request.GET.get('token', None))
        all_tokens_set.update(getattr(request.user, 'allowed_tokens', []))
        all_tokens_set.update(request.session.get('allowed_tokens', []))
        all_tokens_list = list(all_tokens_set)
        request.user.allowed_tokens = all_tokens_list
        request.session['allowed_tokens'] = all_tokens_list
