# -*- coding: utf-8 -*-


from tardis.tardis_portal.api import (
    default_authentication
)
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie.resources import ModelResource

from .models import SFTPPublicKey


class SFTPACLAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return object_list.filter(user=bundle.request.user)

    def read_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def create_detail(self, object_list, bundle):
        if bundle.request.user.is_authenticated():
            return bundle.obj.user == bundle.request.user

        raise Unauthorized("You must be authenticated to create SSH keys.")

    def delete_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user


class SFTPPublicKeyModelResource(ModelResource):
    """Tastypie model resource"""

    class Meta:
        queryset = SFTPPublicKey.objects.all()
        authentication = default_authentication
        authorization = SFTPACLAuthorization()
        resource_name = 'sftp/key'
        filtering = {
            'id': ('exact',),
            'name': ('exact',),
        }
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'post', 'delete']
