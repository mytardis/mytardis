from tardis.default_settings import USER_MENU_MODIFIERS

SFTP_PORT = 2200
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

USER_MENU_MODIFIERS.extend([
    'tardis.apps.sftp.user_menu_modifiers.add_ssh_keys_menu_item'
])
'''
Adds a user menu item to access the SFTP key management page.
'''

REQUIRE_SSL_TO_GENERATE_KEY = True
'''
Require a secure connection (i.e., HTTPS) to allow key generation.
'''
