DEBUG = True
"""Set to false for production use"""

ALLOWED_HOSTS = ["*"]
"""
For security reasons this needs to be set to your hostname and/or IP
address in production.
"""

INTERNAL_IPS = ("127.0.0.1",)
"""
A list of IP addresses, as strings, that:
    Allow the debug() context processor to add some variables to the
    template context.
"""
