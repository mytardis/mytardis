# -*- coding: utf-8 -*-

import base64
from binascii import hexlify

from paramiko import DSSKey, ECDSAKey, RSAKey
from tastypie.authorization import Authorization
from tastypie.exceptions import HydrationError, Unauthorized
from tastypie.resources import ModelResource

from tardis.tardis_portal.api import default_authentication

from .forms import key_add_form
from .models import SFTPPublicKey


class SFTPACLAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return object_list.filter(user=bundle.request.user)

    def read_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def create_detail(self, object_list, bundle):
        if bundle.request.user.is_authenticated:
            return bundle.obj.user == bundle.request.user

        raise Unauthorized("You must be authenticated to create SSH keys.")

    def delete_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user


class SFTPPublicKeyAppResource(ModelResource):
    """Tastypie model resource for SFTPPublicKey model"""

    class Meta:
        queryset = SFTPPublicKey.objects.all()
        authentication = default_authentication
        authorization = SFTPACLAuthorization()
        validation = key_add_form
        resource_name = "publickey"
        filtering = {
            "id": ("exact",),
            "name": ("exact",),
        }
        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get", "delete"]

    def hydrate(self, bundle):
        # Add user to bundle as this doesn't come from client
        bundle.obj.user = bundle.request.user
        return bundle

    def dehydrate(self, bundle):
        if bundle.obj.key_type == "ssh-rsa":
            key = RSAKey(data=base64.b64decode(bundle.obj.public_key))
        elif bundle.obj.key_type == "ssh-dss":
            key = DSSKey(data=base64.b64decode(bundle.obj.public_key))
        elif bundle.obj.key_type.startswith("ecdsa"):
            key = ECDSAKey(data=base64.b64decode(bundle.obj.public_key))
        else:
            raise HydrationError("Unknown key type: %s" % bundle.object.key_type)

        bundle.data["fingerprint"] = hexlify(key.get_fingerprint()).decode(
            encoding="utf-8"
        )

        return bundle
