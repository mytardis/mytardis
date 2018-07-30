'''
Accounts URLs
'''
from django.conf.urls import include, url
from registration.backends.default.views import RegistrationView

from tardis.tardis_portal.views import (
    manage_user_account,
    manage_auth_methods
)

accounts_urls = [
    url(r'^manage$', manage_user_account,
        name='tardis.tardis_portal.views.manage_user_account'),
    url(r'^manage_auth_methods/$', manage_auth_methods,
        name='tardis.tardis_portal.views.manage_auth_methods'),
    url(r'^register/$', RegistrationView.as_view(),  # pylint: disable=E1120
        name='tardis.tardis_portal.views.register'),
    url(r'', include('registration.backends.default.urls')),
]
