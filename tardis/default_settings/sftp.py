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
