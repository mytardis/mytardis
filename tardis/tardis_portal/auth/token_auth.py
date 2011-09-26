"""
token authentication module
"""

from django.conf import settings
from django.contrib.auth.models import User
from tardis.tardis_portal.models import Token, ExperimentACL, Experiment
from tardis.tardis_portal.auth.interfaces import GroupProvider

TOKEN_EXPERIMENT = '_token_experiment'


def _ensure_acl_exists(experiment_id):
    experiment = Experiment.objects.get(pk=experiment_id)

    ExperimentACL.objects.get_or_create(pluginId=TokenGroupProvider.name,
        entityId=str(experiment.id), canRead=True, experiment=experiment,
        aclOwnershipType=ExperimentACL.OWNER_OWNED)


def authenticate(request, token_string):
    try:
        token = Token.objects.get(token=token_string)
    except Token.DoesNotExist:
        return None
    else:
        if token.is_expired():
            return None

    user = User.objects.get(username=settings.TOKEN_USERNAME)
    user.backend = 'django.contrib.auth.backends.ModelBackend'

    request.session[TOKEN_EXPERIMENT] = token.experiment.id
    _ensure_acl_exists(token.experiment.id)
    request.session.set_expiry(token.get_session_expiry())

    return user


class TokenGroupProvider(GroupProvider):
    name = u'token_group'

    def getGroups(self, request):
        if request.user.is_authenticated() and \
                TOKEN_EXPERIMENT in request.session:
            return [str(request.session[TOKEN_EXPERIMENT])]
        else:
            return []

    def searchGroups(self, **kwargs):
        """
            return nothing because these are not groups in
            the standard sense
        """
        return []
