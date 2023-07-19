import importlib
import sys

from django.conf import settings

this_module = sys.modules[__name__]


try:
    installed_apps = getattr(settings, "INSTALLED_APPS", [])
except Exception as e:
    installed_apps = []

for app in installed_apps:
    if app.startswith("tardis.apps"):
        try:
            app_module = importlib.import_module("%s.default_settings" % app)
            # print("Loading default settings for %s" % app)
            for setting in dir(app_module):
                if setting.isupper():
                    # print(" - %s" % setting)
                    setattr(this_module, setting, getattr(app_module, setting))
        except Exception as e:
            # print("Can't load default settings for %s due to:\n%s" % (app, str(e)))
            pass
