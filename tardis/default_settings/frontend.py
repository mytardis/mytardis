from os import path

# Render image file size limit: zero means no limit
RENDER_IMAGE_SIZE_LIMIT = 0

# Max number of images in dataset view's carousel: zero means no limit
MAX_IMAGES_IN_CAROUSEL = 100

BLEACH_ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'code',
    'em',
    'i',
    'li',
    'ol',
    'strong',
    'ul',
]
'''
These are the default bleach values and shown here as an example.
'''

BLEACH_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
}
'''
These are the default bleach values and shown here as an example.
'''

# Used in "My Data" view:
OWNED_EXPS_PER_PAGE = 20
SHARED_EXPS_PER_PAGE = 20

# Javascript settings
ANGULARJS_VERSION = "1.6.5"
ANGULAR_MATERIAL_VERSION = "1.1.4"
NGDIALOG_VERSION = "0.3.4"
NG_MULTIPLE_SELECT_VERSION = "1.1.2"
