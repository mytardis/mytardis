UPLOAD_METHOD = False
"""
Old version: UPLOAD_METHOD = "uploadify".
This can be changed to an app that provides an upload_button function,
eg. "tardis.apps.filepicker.views.upload_button" to use a fancy
commercial uploader.
To use filepicker, please also get an API key at http://filepicker.io
"""
# FILEPICKER_API_KEY = "YOUR KEY"

# New in Django 1.10:
DATA_UPLOAD_MAX_MEMORY_SIZE = 262144000  # 250 MB
