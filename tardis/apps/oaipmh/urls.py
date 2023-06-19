from django.urls import re_path

from .views import endpoint

urlpatterns = [
    re_path(r"^$", endpoint, name="oaipmh-endpoint"),
]
