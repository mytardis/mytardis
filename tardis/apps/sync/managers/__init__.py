from django.utils import importlib
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import os.path

# load_manager() method was failing on django 1.4
# replacing it for now.. - steve
# TODO: fix
manager = getattr(importlib.import_module('tardis.apps.sync.%s' % settings.SYNC_MANAGER), 'SyncManager')