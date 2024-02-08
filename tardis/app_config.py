import re

from django.apps import AppConfig, apps
from django.conf import settings
from django.core.checks import Error, register

import six


class AbstractTardisAppConfig(AppConfig):
    """
    All MyTardis app configuration classes should extend this abstract class
    to have their APIs and URLs automatically added to URL routing.
    """

    # Override this in subclasses to define any apps that this app depends on
    app_dependencies = []


def is_tardis_app(app_config):
    """
    Determines whether the installed app is a MyTardis app

    :param app_config: the AppConfig object of an installed app
    :type app_config: AppConfig
    :return: True if the app is a MyTardis app, False otherwise
    :rtype: bool
    """
    if app_config.name.startswith(settings.TARDIS_APP_ROOT):
        return True
    return isinstance(app_config, AbstractTardisAppConfig)


def format_app_name_for_url(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower())


def get_tardis_apps():
    """
    Gets a list of tuples where the first element is the app name, and the
    second is the module path

    :return: a list of tardis apps
    :rtype: list of apps
    """
    tardis_apps = []
    for app_name, app_config in apps.app_configs.items():
        if is_tardis_app(app_config) and app_config.name in settings.INSTALLED_APPS:
            tardis_apps.append((app_name, app_config.name))
    return tardis_apps


@register()
def check_app_dependencies(app_configs, **kwargs):
    """
    Checks currently installed apps for dependencies required by installed apps
    as defined by the app_dependencies attribute of the AppConfig object, if
    present.

    :param app_configs: a list of app_configs to check, or None for all apps to
     be checked
    :type app_configs: AppConfig
    :param kwargs: unknown list of args
    :type kwargs: list of args
    :return: a list of unsatisfied dependencies
    :rtype: list of strings
    """

    installed_apps = {
        app_config.name: app_config for app_config in six.itervalues(apps.app_configs)
    }

    # According to https://docs.djangoproject.com/en/1.8/topics/checks/#writing-your-own-checks
    # app_configs may contain a list of apps to check, but if it's None, all
    # apps should be inspected.
    if app_configs:
        apps_to_check = six.itervalues(app_configs)
    else:
        apps_to_check = six.itervalues(installed_apps)

    errors = []
    for app in apps_to_check:
        deps = getattr(app, "app_dependencies", [])
        for dependency in deps:
            if not installed_apps.has_key(dependency):
                errors.append(
                    Error(
                        "Could not find dependent app: %s" % dependency,
                        hint='Add "%s" to INSTALLED_APPS' % dependency,
                        obj=app,
                    )
                )
    return errors
