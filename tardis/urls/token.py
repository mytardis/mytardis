'''
Token URLs
'''
from django.conf.urls import url

from tardis.tardis_portal.views import token_delete

token_urls = [
    url(r'^delete/(?P<token_id>.+)/', token_delete,
        name='tardis.tardis_portal.views.token_delete'),
]
