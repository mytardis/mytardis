# pylint: disable=wildcard-import

# first apps, so other files can add to INSTALLED_APPS
from .apps import *

from .admins import *
from .analytics import *
from .auth import *
from .caches import *
from .celery_settings import *
from .custom_views import *
from .database import *
from .debug import *
from .downloads import *
from .email import *
from .filters import *
from .frontend import *
from .i18n import *
from .localisation import *
from .logging import *
from .middlewares import *
from .publication import *
from .search import *
from .sharing import *
from .site_customisations import *
from .static_files import *
from .storage import *
from .templates import *
from .uploads import *
from .urls import *

# Default enabled app settings
from ..apps.sftp.default_settings import *


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
