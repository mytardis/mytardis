from os import path

from .storage import DEFAULT_STORAGE_BASE_DIR

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = DEFAULT_STORAGE_BASE_DIR

# Used by "django collectstatic"
STATIC_ROOT = path.abspath(path.join(path.dirname(__file__), "../..", "static"))

# Use cachable copies of static files
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# used by webpack
STATICFILES_DIRS = (path.abspath(path.join(path.dirname(__file__), "../..", "assets")),)

WEBPACK_LOADER = {
    "DEFAULT": {
        "BUNDLE_DIR_NAME": "bundles/",
        "STATS_FILE": path.join(
            path.abspath(path.join(path.dirname(__file__), "../..")),
            "webpack-stats.json",
        ),
    }
}
