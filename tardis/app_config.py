from importlib import import_module

import re
from django.apps import AppConfig
from django.conf import settings

DEFAULT_APP_CONFIG = 'default_app_config'


class AbstractTardisAppConfig(AppConfig):
    """
    All MyTardis app configuration classes should extend this abstract class
    to have their APIs and URLs automatically added to URL routing.
    """
    pass


def get_app_and_config_class(app):
    """
    Gets the app module and configuration class if available
    :param app: a string reference to the app module
    :return: a tuple containing the app module and configuration class,
    respectively.
    """
    app_module = import_module(app)
    config_class = None
    if hasattr(app_module, DEFAULT_APP_CONFIG):
        module_name, class_name = getattr(app_module,
                                          DEFAULT_APP_CONFIG).rsplit('.',
                                                                     1)
        config_class = getattr(import_module(module_name), class_name)
    return app_module, config_class


def get_app_name(app):
    """
    Gets the app's name
    :param app: a string reference to the app module
    :return: the app's name
    """
    app_module, config_class = get_app_and_config_class(app)

    if config_class is not None:
        name = config_class.verbose_name
    elif app.startswith(settings.TARDIS_APP_ROOT):
        name = app.split('.').pop()
    else:
        name = app

    # Replaces any non A-Z characters with a dash (-)
    return re.sub(r'[^a-z]+', '-', name.lower())


def is_tardis_app(app):
    """
    Determines whether the installed app is a MyTardis app
    :param app: a string reference to the app module
    :return: True if the app is a MyTardis app, False otherwise
    """
    if app.startswith(settings.TARDIS_APP_ROOT):
        return True
    app_module, config_class = get_app_and_config_class(app)
    if config_class is not None:
        return issubclass(config_class, AbstractTardisAppConfig)
    return False


def get_tardis_apps():
    return [(get_app_name(app), app) for app in settings.INSTALLED_APPS if
            is_tardis_app(app)]
