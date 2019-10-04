from django.conf.urls import url

from .views import endpoint


urlpatterns = [
    url(r'^$', endpoint, name="oaipmh-endpoint"),
]
