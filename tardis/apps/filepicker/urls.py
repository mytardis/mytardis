from django.conf import settings
from django.conf.urls import url

from .views import upload_button
from .views import fpupload

urlpatterns = []

if not settings.DISABLE_CREATION_FORMS:
    urlpatterns += [
        url(
            r"^upload_button/(?P<dataset_id>\d+)/$",
            upload_button,
            name="tardis.apps.filepicker.views.upload_button",
        ),
        url(
            r"^fpupload/(?P<dataset_id>\d+)/$",
            fpupload,
            name="tardis.apps.filepicker.views.fpupload",
        ),
    ]
