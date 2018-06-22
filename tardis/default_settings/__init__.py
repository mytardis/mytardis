# pylint: disable=wildcard-import

# first apps, so other files can add to INSTALLED_APPS
from tardis.default_settings.apps import *

from tardis.default_settings.admins import *
from tardis.default_settings.analytics import *
from tardis.default_settings.auth import *
from tardis.default_settings.caches import *
from tardis.default_settings.celery import *
from tardis.default_settings.custom_views import *
from tardis.default_settings.database import *
from tardis.default_settings.debug import *
from tardis.default_settings.downloads import *
from tardis.default_settings.email import *
from tardis.default_settings.filters import *
from tardis.default_settings.frontend import *
from tardis.default_settings.i18n import *
from tardis.default_settings.localisation import *
from tardis.default_settings.logging import *
from tardis.default_settings.middlewares import *
from tardis.default_settings.publication import *
from tardis.default_settings.search import *
from tardis.default_settings.sftp import *
from tardis.default_settings.sharing import *
from tardis.default_settings.site_customisations import *
from tardis.default_settings.staging import *
from tardis.default_settings.static_files import *
from tardis.default_settings.storage import *
from tardis.default_settings.templates import *
from tardis.default_settings.uploads import *
from tardis.default_settings.urls import *


# Get version from git to be displayed on About page.
def get_git_version():
    repo_dir = path.dirname(path.dirname(path.abspath(__file__)))

    def run_git(args):
        import subprocess
        process = subprocess.Popen('git %s' % args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True,
                                   cwd=repo_dir,
                                   universal_newlines=True)
        return process.communicate()[0]

    try:
        info = {
            'commit_id': run_git("log -1 --format='%H'").strip(),
            'date': run_git("log -1 --format='%cd' --date=rfc").strip(),
            'branch': run_git("rev-parse --abbrev-ref HEAD").strip(),
            'tag': run_git("describe --abbrev=0 --tags").strip(),
        }
    except Exception:
        return ["unavailable"]
    return info

MYTARDIS_VERSION = get_git_version()
