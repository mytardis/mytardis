"""
token authentication module
"""

from django.conf import settings
from django.contrib.auth.models import User
from tardis.tardis_portal.models import Token, ObjectACL, Experiment
from tardis.tardis_portal.auth.interfaces import GroupProvider

TOKEN_EXPERIMENT = '_token_experiment'


def _ensure_acl_exists(experiment_id):
    experiment = Experiment.objects.get(pk=experiment_id)

    ObjectACL.objects.get_or_create(
        pluginId=TokenGroupProvider.name,
        entityId=str(experiment.id), canRead=True,
        content_type=experiment.get_ct(),
        object_id=experiment.id,
        aclOwnershipType=ObjectACL.OWNER_OWNED)


class TokenGroupProvider(GroupProvider):
    '''
    Transforms tokens into auth groups
    '''
    name = u'token_group'

    def getGroups(self, user):
        if hasattr(user, 'allowed_tokens'):
            tokens = Token.objects.filter(
                token__in=user.allowed_tokens)
            experiment_ids = []
            for token in tokens:
                if not token.is_expired():
                    _ensure_acl_exists(token.experiment.id)
                    experiment_ids.append(token.experiment.id)
            return experiment_ids
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
        return None
