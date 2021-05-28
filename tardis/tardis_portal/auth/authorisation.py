'''
Object-level authorisation backend

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
'''
from datetime import datetime

from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from ..models.access_control import ExperimentACL, DatasetACL, DatafileACL
from .token_auth import TokenGroupProvider


class ACLAwareBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    app_label = 'tardis_acls'

    def authenticate(self, request):
        '''
        do not use this backend for authentication
        '''
        return None

    def get_perm_bool(self, verb):
        '''
        relates ACLs to permissions
        '''
        if verb in ('change'):
            return Q(canWrite=True) | Q(isOwner=True)
        if verb in ('view'):
            return Q(canRead=True) | Q(isOwner=True)
        if verb in ('delete',):
            return Q(canDelete=True) | Q(isOwner=True)
        if verb in ('owns', 'share'):
            return Q(isOwner=True)
        return Q()

    def has_perm(self, user_obj, perm, obj=None):
        '''
        main method, calls other methods based on permission type queried
        '''
        if not user_obj.is_authenticated:
            allowed_tokens = getattr(user_obj, 'allowed_tokens', [])
            user_obj = AnonymousUser()
            user_obj.allowed_tokens = allowed_tokens

        if obj is None:
            return False

        try:
            perm_label, perm_type = perm.split('.')
            # the following is necessary because of the ridiculous naming
            # of 'Dataset_File'...... which has since been renamed, so this
            # can be changed back soon
            type_list = perm_type.split('_')
            perm_action = type_list[0]
            perm_ct = '_'.join(type_list[1:])
        except:
            return False

        if perm_label != self.app_label:
            return False

        if perm_type == 'change_experiment' and \
                not user_obj.has_perm('tardis_portal.change_experiment'):
            return False

        ct = ContentType.objects.get_for_model(obj)
        if ct.model != perm_ct:
            return False

        method_name = '_has_%s_perm' % perm_action

        # run any custom perms per model, continue if not None
        # allows complete overriding of standard authorisation, eg for public
        # experiments
        model_spec_perm = getattr(obj, method_name,
                                  lambda *args, **kwargs: None)(user_obj)
        if isinstance(model_spec_perm, bool):
            return model_spec_perm
        if model_spec_perm is not None:
            # pass auth to a different object, if False try this ACL
            # works when returned object is parent.
            # makes it impossible to 'hide' child objects
            if not isinstance(model_spec_perm, (list, set, QuerySet)):
                model_spec_perm = [model_spec_perm]
            for msp in model_spec_perm:
                new_ct = ContentType.objects.get_for_model(msp)
                new_perm = '%s.%s_%s' % (perm_label, perm_action, new_ct)
                if user_obj.has_perm(new_perm, msp):
                    return True

        # get_acls
        obj_acls = ObjectACL.objects\
            .filter(content_type=ct, object_id=obj.id)\
            .filter(self.get_perm_bool(perm_action))\
            .filter(ObjectACL.get_effective_query())

        query = Q(pluginId='django_user',
                  entityId=str(user_obj.id))

        if user_obj.is_authenticated:
            for name, group in user_obj.userprofile.ext_groups:
                query |= Q(pluginId=name, entityId=str(group))
        else:
            # the only authorisation available for anonymous users is tokenauth
            tgp = TokenGroupProvider()
            for group in tgp.getGroups(user_obj):
                query |= Q(pluginId=tgp.name, entityId=str(group))

        return obj_acls.filter(query).count() > 0
