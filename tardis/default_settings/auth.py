USER_PROVIDERS = ("tardis.tardis_portal.auth.localdb_auth.DjangoUserProvider",)

GROUP_PROVIDERS = (
    "tardis.tardis_portal.auth.localdb_auth.DjangoGroupProvider",
    "tardis.tardis_portal.auth.token_auth.TokenGroupProvider",
)

ONLY_EXPERIMENT_ACLS = True

# For a freshly installed MyTardis DB this will the default User ID,
# as it is created in the migrations prior to any SuperUser creation.
# For existing DBs this will need to be overriden in the settings.py file
PUBLIC_USER_ID = 1

# AUTH_PROVIDERS entry format:
# ('name', 'display name', 'backend implementation')
#   name - used as the key for the entry
#   display name - used as the displayed value in the login form
#   backend implementation points to the actual backend implementation
#
#   In most cases, the backend implementation should be a fully
#   qualified class name string, whose class can be instantiated without
#   any arguments.  For LDAP authentication, the
#       'tardis.tardis_portal.auth.ldap_auth.LDAPBackend'
#   class can't be instantiated without any arguments, so the
#       'tardis.tardis_portal.auth.ldap_auth.ldap_auth'
#   wrapper function should be used instead.
#
# We will assume that localdb will always be a default AUTH_PROVIDERS entry

AUTH_PROVIDERS = (
    ("localdb", "Local DB", "tardis.tardis_portal.auth.localdb_auth.DjangoAuthBackend"),
)


AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "tardis.tardis_portal.auth.authorisation.ACLAwareBackend",
)

MANAGE_ACCOUNT_ENABLED = True
LINK_ACCOUNTS_ENABLED = True

AUTOGENERATE_API_KEY = False
"""
Generate a tastypie API key with user post_save
(tardis/tardis_portal/models/hooks.py)
"""

# default authentication module for experiment ownership user during
# ingestion? Must be one of the above authentication provider names
DEFAULT_AUTH = "localdb"

AUTH_PROFILE_MODULE = "tardis_portal.UserProfile"

# New users are added to these groups by default.
NEW_USER_INITIAL_GROUPS = []

# Turn on/off the self-registration link and form
REGISTRATION_OPEN = True
"""Enable/disable the self-registration link and form in the UI.
Note - this does not actually disable the URL endpoints for registration.
You must also remove the `registration` app from `INSTALLED_APPS` to
disable registration.
"""

ACCOUNT_ACTIVATION_DAYS = 3

# Show the Rapid Connect login button.
RAPID_CONNECT_ENABLED = False

RAPID_CONNECT_CONFIG = {}

RAPID_CONNECT_CONFIG["secret"] = "CHANGE_ME"
RAPID_CONNECT_CONFIG["authnrequest_url"] = ""
"""something like
'https://rapid.test.aaf.edu.au/jwt/authnrequest/research/XXXXXXXXXXXXXXXX'
"""

RAPID_CONNECT_CONFIG["iss"] = "https://rapid.test.aaf.edu.au"
""" 'https://rapid.test.aaf.edu.au' or 'https://rapid.aaf.edu.au'
"""
RAPID_CONNECT_CONFIG["aud"] = "https://example.com/rc/"
"""Public facing URL that accepts the HTTP/HTTPS POST request from
Rapid Connect.
"""
# settings for login URL
LOGIN_URL = "/login/"

# setting for logout redirect URL
LOGOUT_REDIRECT_URL = "/"

# disable /accounts/login
INCLUDE_AUTH_URLS = False


#################
# LDAP settings #
#################
# To use LDAP, add 'tardis.tardis_portal.auth.ldap_auth.ldap_auth'
# to AUTH_PROVIDERS, e.g.
# AUTH_PROVIDERS = (
#    ('ldap', 'LDAP',
#     'tardis.tardis_portal.auth.ldap_auth.ldap_auth'),
# )
LDAP_USE_TLS = False
LDAP_URL = "ldap://localhost:38911/"

LDAP_USER_LOGIN_ATTR = "uid"
LDAP_USER_ATTR_MAP = {"givenName": "first_name", "sn": "last_name", "mail": "email"}
LDAP_GROUP_ID_ATTR = "cn"
LDAP_GROUP_ATTR_MAP = {"description": "display"}

LDAP_ADMIN_USER = ""
LDAP_ADMIN_PASSWORD = ""
LDAP_BASE = "dc=example, dc=com"
LDAP_USER_BASE = "ou=People, " + LDAP_BASE
LDAP_GROUP_BASE = "ou=Group, " + LDAP_BASE
