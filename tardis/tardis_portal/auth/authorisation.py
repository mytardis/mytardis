'''
Object-level authorisation backend

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
'''
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType

class ACLAwareBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    app_label = 'tardis_acls'

    def authenticate(self, username, password):
        '''
        do not use this backend for authentication
        '''
        return None

    def has_perm(self, user_obj, perm, obj=None):
        '''
        main method, calls other methods based on permission type queried
        '''
        if not user_obj.is_authenticated():
            user_obj = AnonymousUser()

        if obj is None:
            return False

        try:
            perm_label, perm_type = perm.split('.')
            perm_action, perm_ct = perm_type.split('_')
        except:
            return False

        if perm_label != self.app_label:
            return False

        ct = ContentType.objects.get_for_model(obj)
        if ct.name != perm_ct:
            return False

        method_name = 'has_%s_perm' % perm_action

        if hasattr(obj, method_name):
            return getattr(obj, method_name)(user_obj)

        perm_method = getattr(self, method_name,
                              lambda *args, **kwargs: False)
        return perm_method(user_obj, obj)

    def has_read_perm(self, user_obj, obj):
        return False

    def has_change_perm(self, user_obj, obj):
        return False
