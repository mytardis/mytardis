from django.conf import settings

filepicker_api_key = getattr(settings, "FILEPICKER_API_KEY", "")
