"""
Minimal urls.py, so we can do a reverse lookup for
the 's3_api_download_dfo' URL pattern.

's3_api_download_dfo' is defined in the prepend_urls
method of the ReplicaAppResource class in api.py

The API endpoint defined in this app is mapped to a
URL in tardis/urls/api.py (along with API endpoints
defined by other MyTardis apps).
"""
urlpatterns = []
