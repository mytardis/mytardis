from django.apps import AppConfig


class AbstractTardisAppConfig(AppConfig):
    """
    All MyTardis app configuration classes should extend this abstract class
    to have their APIs and URLs automatically added to URL routing.
    """
    pass
