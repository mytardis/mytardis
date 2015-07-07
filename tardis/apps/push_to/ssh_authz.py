import base64
import json
from StringIO import StringIO
from paramiko import RSACert
import requests


def sign_certificate(credential, token, url):
    """
    An interface to the OAuth2 SSH certificate signing service
    @type credential: models.Credential
    """
    key_type = credential.key.get_name()
    key_data = credential.key.get_base64()
    headers = {'Authorization': 'Bearer ' + token}
    payload = {'public_key': key_type + ' ' + key_data}

    # TODO: remote verify=False
    r = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        verify=False)
    cert_response = json.loads(r.text)
    if 'certificate' not in cert_response:
        return False

    # Ignore the certificate comment field
    cert_type, cert_data = cert_response['certificate'].split()[0:2]
    if cert_type != 'ssh-rsa-cert-v01@openssh.com':
        return False  # We only support this certificate type at the moment

    old_key = credential.key
    private_key = StringIO()
    old_key.write_private_key(private_key)
    private_key.seek(0)
    cert = RSACert(
        data=base64.b64decode(cert_data),
        privkey_file_obj=private_key)
    credential.key = cert
    credential.save()
    return True
