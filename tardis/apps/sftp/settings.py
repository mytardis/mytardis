from tardis.default_settings import TEMPLATES

SFTP_PORT = 2200
SFTP_GEVENT = False
# SFTP_HOST_KEY = (
#     "-----BEGIN RSA PRIVATE KEY-----\n"
#     "...\n"
#     "-----END RSA PRIVATE KEY-----\n")
SFTP_HOST_KEY = ""

SFTP_USERNAME_ATTRIBUTE = 'email'
'''
The attribute from the User model ('email' or 'username') used to generate
the SFTP login example on the sftp_access help page.
'''

TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'tardis.apps.sftp.context_processors.sftp_menu_processor'
])
