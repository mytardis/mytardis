'''
Object-level authorisation backend

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
'''
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.query import QuerySet

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

        if settings.ONLY_EXPERIMENT_ACLS:
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


        if ct.model == 'experiment':
            # the only authorisation available for anonymous users is tokenauth
            tgp = TokenGroupProvider()
            query = ExperimentACL.objects.none()
            for token in tgp.getGroups(user_obj):
                query |= token.experimentacls.select_related("experiment"
                                         ).filter(experiment__id=obj.id).filter(self.get_perm_bool(perm_action)
                                         ).exclude(effectiveDate__gte=datetime.today(),
                                                   expiryDate__lte=datetime.today())
            if user_obj.is_authenticated:
                query |= user_obj.experimentacls.select_related("experiment"
                                         ).filter(experiment__id=obj.id).filter(self.get_perm_bool(perm_action)
                                         ).exclude(effectiveDate__gte=datetime.today(),
                                                   expiryDate__lte=datetime.today())
                for group in user_obj.groups.all():
                    query |= group.experimentacls.select_related("experiment"
                                             ).filter(experiment__id=obj.id).filter(self.get_perm_bool(perm_action)
                                             ).exclude(effectiveDate__gte=datetime.today(),
                                                       expiryDate__lte=datetime.today())
            return query.exists()

        #TODO need to write the auth method for EXP_ONLY datasets and datafiles
        if not settings.ONLY_EXPERIMENT_ACLS:
            if ct.model == 'dataset':
                # the only authorisation available for anonymous users is tokenauth
                tgp = TokenGroupProvider()
                query = DatasetACL.objects.none()
                for token in tgp.getGroups(user_obj):
                    query |= token.datasetacls.select_related("dataset"
                                             ).filter(dataset__id=obj.id).filter(self.get_perm_bool(perm_action)
                                             ).exclude(effectiveDate__gte=datetime.today(),
                                                       expiryDate__lte=datetime.today())
                if user_obj.is_authenticated:
                    query |= user_obj.datasetacls.select_related("dataset"
                                             ).filter(dataset__id=obj.id).filter(self.get_perm_bool(perm_action)
                                             ).exclude(effectiveDate__gte=datetime.today(),
                                                       expiryDate__lte=datetime.today())
                    for group in user_obj.groups.all():
                        query |= group.datasetacls.select_related("dataset"
                                                 ).filter(dataset__id=obj.id).filter(self.get_perm_bool(perm_action)
                                                 ).exclude(effectiveDate__gte=datetime.today(),
                                                           expiryDate__lte=datetime.today())
                return query.exists()

            if ct.model.replace(' ','') == 'datafile':
                # the only authorisation available for anonymous users is tokenauth
                tgp = TokenGroupProvider()
                query = DatafileACL.objects.none()
                for token in tgp.getGroups(user_obj):
                    query |= token.datafileacls.select_related("datafile"
                                             ).filter(datafile__id=obj.id).filter(self.get_perm_bool(perm_action)
                                             ).exclude(effectiveDate__gte=datetime.today(),
                                                       expiryDate__lte=datetime.today())
                if user_obj.is_authenticated:
                    query |= user_obj.datafileacls.select_related("datafile"
                                             ).filter(datafile__id=obj.id).filter(self.get_perm_bool(perm_action)
                                             ).exclude(effectiveDate__gte=datetime.today(),
                                                       expiryDate__lte=datetime.today())
                    for group in user_obj.groups.all():
                        query |= group.datafileacls.select_related("datafile"
                                                 ).filter(datafile__id=obj.id).filter(self.get_perm_bool(perm_action)
                                                 ).exclude(effectiveDate__gte=datetime.today(),
                                                           expiryDate__lte=datetime.today())
                return query.exists()


        return False
