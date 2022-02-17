RENDER_IMAGE_SIZE_LIMIT = 0
"""
Render image file size limit: zero means no limit
"""

RENDER_IMAGE_DATASET_SIZE_LIMIT = 0
"""
Render image dataset size limit: zero means no limit

In order to display a dataset thumbnail image, MyTardis queries the dataset's
files for image MIME types.  These queries can be very slow for large
datasets, making page load times slow.  In future versions, the dataset
thumbnails will be generated asynchronously (not at response time), but for
now, we can set RENDER_IMAGE_DATASET_SIZE_LIMIT to the maximum number of files
a dataset can have for MyTardis to scan it for image files at response time.
"""

MAX_IMAGES_IN_CAROUSEL = 100
"""
Max number of images in dataset view's carousel: zero means no limit
"""

BLEACH_ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
]
"""
These are the default bleach values and shown here as an example.
"""

BLEACH_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "abbr": ["title"],
    "acronym": ["title"],
}
"""
These are the default bleach values and shown here as an example.
"""

# Used in "My Data" view:
OWNED_EXPS_PER_PAGE = 20

# Used in "Shared" view:
SHARED_EXPS_PER_PAGE = 20

# Used in both "My Data" and "Shared" view:
EXPS_EXPAND_ACCORDION = 5

# Used in "Experiment" view:
DATASET_ORDERING = "description"
SHOW_DATASET_THUMBNAILS = True

# Setting to globally disable all exp/set/file creation (add) buttons
# on the MyTardis web UI. API uneffected
DISABLE_CREATION_FORMS = False
