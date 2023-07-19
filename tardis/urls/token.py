"""
Token URLs
"""
from django.urls import re_path

from tardis.tardis_portal.views import token_delete

token_urls = [
    re_path(
        r"^delete/(?P<token_id>.+)/",
        token_delete,
        name="tardis.tardis_portal.views.token_delete",
    ),
]
