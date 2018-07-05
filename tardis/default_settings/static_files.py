from os import path
from tardis.default_settings.storage import DEFAULT_STORAGE_BASE_DIR

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = DEFAULT_STORAGE_BASE_DIR

# Used by "django collectstatic"
STATIC_ROOT = path.abspath(path.join(path.dirname(__file__), '../..', 'static'))

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = STATIC_URL + '/admin/'
def get_admin_media_path():
    import pkgutil
    package = pkgutil.get_loader("django.contrib.admin")
    return path.join(package.filename, 'static', 'admin')

ADMIN_MEDIA_STATIC_DOC_ROOT = get_admin_media_path()

STATICFILES_DIRS = (
    ('admin', ADMIN_MEDIA_STATIC_DOC_ROOT),
)

# Use cachable copies of static files
STATICFILES_STORAGE = \
    'django.contrib.staticfiles.storage.CachedStaticFilesStorage'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'npm.finders.NpmFinder',
)

# django-npm settings:
NPM_ROOT_PATH = path.abspath(path.join(path.dirname(__file__), '../..'))

# If you have run "npm install", rather than "npm install --production",
# you will get a lot of devDependencies installed in node_modules/ which
# are only needed for development/testing (e.g. "npm test") and don't
# need to be copied when running collectstatic.  NPM_FILE_PATTERNS
# specifies the folders within node_modules/ which do need to be copied:
NPM_FILE_PATTERNS = {
    'angular': ['*'],
    'angular-resource': ['*'],
    'jquery': ['*'],
    'jquery-migrate': ['*'],
    'ng-dialog': ['*'],
    'jquery-ui-dist': ['jquery-ui.min.js']
}
NPM_STATIC_FILES_PREFIX = path.join('js', 'lib')
