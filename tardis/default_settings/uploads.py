from tardis.default_settings.urls import MEDIA_URL, STATIC_URL

UPLOAD_METHOD = False
'''
Old version: UPLOAD_METHOD = "uploadify".
This can be changed to an app that provides an upload_button function,
eg. "tardis.apps.filepicker.views.upload_button" to use a fancy
commercial uploader.
To use filepicker, please also get an API key at http://filepicker.io
'''
# FILEPICKER_API_KEY = "YOUR KEY"

# Uploadify root folder path, relative to STATIC root
UPLOADIFY_PATH = '%s/%s' % (STATIC_URL, 'js/lib/uploadify')

# Upload path that files are sent to
UPLOADIFY_UPLOAD_PATH = '%s/%s' % (MEDIA_URL, 'uploads')
