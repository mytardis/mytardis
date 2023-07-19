from django.conf import settings
from django.urls import re_path

from .views import fpupload, upload_button

urlpatterns = []

if not settings.DISABLE_CREATION_FORMS:
    urlpatterns += [
        re_path(
            r"^upload_button/(?P<dataset_id>\d+)/$",
            upload_button,
            name="tardis.apps.filepicker.views.upload_button",
        ),
        re_path(
            r"^fpupload/(?P<dataset_id>\d+)/$",
            fpupload,
            name="tardis.apps.filepicker.views.fpupload",
        ),
    ]
