from importlib import import_module

import re
from django.apps import AppConfig
from django.conf import settings
from django.apps import apps


class AbstractTardisAppConfig(AppConfig):
    """
    All MyTardis app configuration classes should extend this abstract class
    to have their APIs and URLs automatically added to URL routing.
    """
    pass


def is_tardis_app(app_config):
    """
    Determines whether the installed app is a MyTardis app
    :param app_config: the AppConfig object of an installed app
    :return: True if the app is a MyTardis app, False otherwise
    """
    if app_config.name.startswith(settings.TARDIS_APP_ROOT):
        return True
    return isinstance(app_config, AbstractTardisAppConfig)


def format_app_name_for_url(name):
    return re.sub(r'[^a-z]+', '-', name.lower())


def get_tardis_apps():
    """
    Gets a list of tuples where the first element is the app name, and the
    second is the module path
    :return:
    """
    tardis_apps = []
    for app_name, app_config in apps.app_configs.items():
        if is_tardis_app(app_config):
            tardis_apps.append((app_name, app_config.name))
    return tardis_apps
