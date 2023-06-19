# -*- coding: utf-8 -*-

import base64

from django import forms
from django.utils.translation import ugettext as _

from paramiko import DSSKey, ECDSAKey, RSAKey
from paramiko.ssh_exception import SSHException
from tastypie.validation import FormValidation


class KeyAddForm(forms.Form):
    name = forms.CharField(required=True, max_length=256)
    key_type = forms.CharField(required=True, max_length=100)
    public_key = forms.CharField(required=True, widget=forms.Textarea)

    def clean(self):
        data = super().clean()
        key_type = data.get('key_type')
        public_key = data.get('public_key')

        try:
            if key_type == "ssh-rsa":
                k = RSAKey(data=base64.b64decode(public_key))
            elif key_type == "ssh-dss":
                k = DSSKey(data=base64.b64decode(public_key))
            elif key_type.startswith('ecdsa'):
                k = ECDSAKey(data=base64.b64decode(public_key))
            else:
                raise forms.ValidationError(
                    _("Unsupport key type: %(keytype)s"),
                    code='invalid keytype',
                    params={'key_type': key_type}
                )

            data['key_type'] = k.get_name()
            data['public_key'] = k.get_base64()

        except (TypeError, SSHException, UnicodeDecodeError) as err:
            if len(public_key) > 30:
                body = public_key[0:30]
            else:
                body = public_key

            raise forms.ValidationError(
                _("Body of SSH public key is invalid:\n%(body)s\n"
                  "Error: %(err)s"),
                code='invalid key body',
                params={'body': body + "...", 'err': err}
            )

        return data


key_add_form = FormValidation(form_class=KeyAddForm)


class KeyGenerateForm(forms.Form):
    name = forms.CharField(required=True, max_length=256)
