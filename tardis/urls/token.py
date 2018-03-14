'''
Token URLs
'''
from django.conf.urls import url

from tardis.tardis_portal.views import (
    token_login,
    token_delete
)

token_urls = [
    url(r'^login/(?P<token>.+)/', token_login),
    url(r'^delete/(?P<token_id>.+)/', token_delete),
]
