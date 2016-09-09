from os import path

STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
                                      '../../var/staging/')).replace('\\', '/')
# SYNC_TEMP_PATH = path.abspath(path.join(path.dirname(__file__),
#     '../var/sync/')).replace('\\', '/')

STAGING_PROTOCOL = 'ldap'
STAGING_MOUNT_PREFIX = 'smb://localhost/staging/'
STAGING_MOUNT_USER_SUFFIX_ENABLE = False
