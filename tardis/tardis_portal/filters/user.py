import logging
import traceback

from tardis.tardis_portal.auth.utils import configure_user


class UserFilter(object):
    """
    A post-save signal can be used to instantiate this filter
    in order to automatically create a UserProfile record with
    isDjangoAccount=True whenever a User record is created,
    and add the new user to settings.NEW_USER_INITIAL_GROUPS
    isDjangoAccount can be later overwritten with False for
    external-only accounts (e.g. LDAP).
    """
    def __call__(self, sender, **kwargs):
        try:
            logger = logging.getLogger(__name__)
            user = kwargs.get('instance')
            userProfile = configure_user(user, isDjangoAccount=True)
        except:
            logger.error(traceback.format_exc())
