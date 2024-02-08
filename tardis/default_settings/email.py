# Email Configuration

EMAIL_HOST = "localhost"
"""
Set this to your local SMTP server, e.g. 'smtp.example.edu'
or to a remote SMTP server, e.g. 'smtp.gmail.com'
"""

EMAIL_PORT = 25
"""
Some SMTP servers require a different port, e.g. 587.
Django's default value for this setting is 25.
"""


EMAIL_HOST_USER = ""
"""
When using a local SMTP server, you probably don't need
to authenticate, so you can leave this blank.

If using a remote SMTP server, this can be set to the
email address used to authenticate, e.g. 'bob@bobmail.com'
"""

EMAIL_HOST_PASSWORD = ""
"""
When using a local SMTP server, you probably don't need
to authenticate, so you can leave this blank.

If using a remote SMTP server, this can be set to the
password used to authenticate.
"""

EMAIL_USE_TLS = False
"""
Some SMTP servers require this to be set to True.
Django's default value for this setting is False.
"""

DEFAULT_FROM_EMAIL = "webmaster@localhost"
"""
This can be set as : "MyTardis Admins <admins@mytardis.org>"
"""
