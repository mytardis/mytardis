"""
Accounts URLs
"""
from django.urls import include, re_path

from registration.backends.default.views import RegistrationView

from tardis.tardis_portal.views import manage_auth_methods, manage_user_account

accounts_urls = [
    re_path(
        r"^manage$",
        manage_user_account,
        name="tardis.tardis_portal.views.manage_user_account",
    ),
    re_path(
        r"^manage_auth_methods/$",
        manage_auth_methods,
        name="tardis.tardis_portal.views.manage_auth_methods",
    ),
    re_path(
        r"^register/$",
        RegistrationView.as_view(),  # pylint: disable=E1120
        name="tardis.tardis_portal.views.register",
    ),
    re_path(r"", include("registration.backends.default.urls")),
]
