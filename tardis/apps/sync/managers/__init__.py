from django.utils import importlib
from django.conf import settings
from django.core import ImproperlyConfigured
import os

class SyncManagerInvalidUIDError(Exception):
    pass

class SyncManagerTransferError(Exception):
    pass

def load_manager():
    
    if not hasattr(settings, 'SYNC_MANAGER'):
        manager_name = 'default_manager'
    else:
        manager_name = settings.SYNC_MANAGER

    try: 
        return importlib.import_module('tardis.apps.sync.%s' % (manager_name))

    except ImportError, e:
        manager_dir = os.path.join(__path__[0], 'managers')

        available_managers = [
                os.path.splittext(f)[0].split("__backend")[0] for f in os.listdir(manager_dir)
                if not f.startswith('_')
                and not f.startswith('.')
                and not f.endswith('.pyc')
                and not f.endswith('.pyo')
                ]

        raise ImproperlyConfigured, '%s is not available. Available choices: %s' %  \
                    (manager_name, ', '.join(available_managers))

manager = load_manager()
