from os import path
from .storage import DEFAULT_STORAGE_BASE_DIR

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = DEFAULT_STORAGE_BASE_DIR

# Used by "django collectstatic"
STATIC_ROOT = path.abspath(path.join(path.dirname(__file__), '../..', 'static'))

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
    'ng-dialog': ['*'],
}

#used by webpack
STATICFILES_DIRS = (
    path.abspath(path.join(path.dirname(__file__), '../..', 'assets')),
)

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bundles/',
        'STATS_FILE': path.join(path.abspath(path.join(path.dirname(__file__), '../..')), 'webpack-stats.json'),
    }
}
