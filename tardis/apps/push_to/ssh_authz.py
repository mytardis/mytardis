import base64
import json
from io import StringIO

import requests
from paramiko import RSAKey
from paramiko.message import Message


def sign_certificate(credential, token, url):
    """
    An interface to the OAuth2 SSH certificate signing service
    @type credential: models.Credential
    """
    key_type = credential.key.get_name()
    key_data = credential.key.get_base64()
    headers = {"Authorization": "Bearer " + token}
    payload = {"public_key": key_type + " " + key_data}

    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=300)
    cert_response = json.loads(r.text)
    if "certificate" not in cert_response:
        return False

    # Ignore the certificate comment field
    remote_user_name = cert_response["user"]
    cert_type, cert_data = cert_response["certificate"].split()[0:2]
    if cert_type != "ssh-rsa-cert-v01@openssh.com":
        return False  # We only support this certificate type at the moment

    old_key = credential.key
    private_key = StringIO()
    old_key.write_private_key(private_key)
    private_key.seek(0)
    cert = RSAKey.from_private_key(private_key)
    cert.load_certificate(Message(base64.b64decode(cert_data)))
    credential.key = cert
    credential.remote_user = remote_user_name
    credential.save()
    return True
