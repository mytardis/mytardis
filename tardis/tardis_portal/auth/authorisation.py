'''
Object-level authorisation backend

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
'''
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from tardis.tardis_portal.models import ObjectACL


class ACLAwareBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    app_label = 'tardis_acls'

    def authenticate(self, username, password):
        '''
        do not use this backend for authentication
        '''
        return None

    def get_perm_bool(self, verb):
        '''
        relates ACLs to permissions
        '''
        if verb in ('add', 'change'):
            return Q(canWrite=True) | Q(isOwner=True)
        elif verb in ('view'):
            return Q(canRead=True) | Q(isOwner=True)
        elif verb in ('delete',):
            return Q(canDelete=True) | Q(isOwner=True)
        elif verb in ('owns',):
            return Q(isOwner=True)
        return Q()

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

        # run any custom perms per model, continue if not None
        # allows complete overriding of standard authorisation, eg for public
        # experiments
        model_spec_perm = getattr(obj, method_name,
                                  lambda *args, **kwargs: None)(user_obj)
        if model_spec_perm is not None:
            return model_spec_perm

        #get_acls
        obj_acls = ObjectACL.objects.filter(
            content_type=ct, object_id=obj.id).filter(
                self.get_perm_bool(perm_action)).filter(
                    ObjectACL.get_effective_query())

        query = Q(pluginId='django_user',
                  entityId=str(user_obj.id))

        for name, group in user_obj.ext_groups:
            query |= Q(pluginId=name, entityId=str(group))

        return obj_acls.filter(query).count() > 0
