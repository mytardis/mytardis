from django.utils import importlib
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import os.path

def load_manager():
    
    manager_class = getattr(settings, 'SYNC_MANAGER_CLASS',
            'tardis.apps.sync.managers.default_manager.SyncManager')
    (module, cls) = manager_class.rsplit('.', 1)

    try: 
        return getattr(importlib.import_module(module), cls)

    except ImportError, e:
        manager_dir = __path__[0]

        available_managers = [
                __import__('tardis.apps.sync.managers.' + os.path.splitext(f)[0]) for f in os.listdir(manager_dir)
                if not f.startswith('_')
                and not f.startswith('.')
                and not f.endswith('.pyc')
                and not f.endswith('.pyo')
                ]

        raise ImproperlyConfigured, '%s is not available. Available choices: %s' %  \
                    (manager_name, ', '.join(available_managers))

manager = load_manager()
