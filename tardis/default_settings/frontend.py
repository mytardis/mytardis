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

# Used in "Shared" view:
SHARED_EXPS_PER_PAGE = 20

# Used in both "My Data" and "Shared" view:
EXPS_EXPAND_ACCORDION = 5

# Used in "Experiment" view:
DATASET_ORDERING = 'description'
SHOW_DATASET_THUMBNAILS = True
