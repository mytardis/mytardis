from tardis.app_config import AbstractTardisAppConfig


class ShibbolethHeaderAuthConfig(AbstractTardisAppConfig):
    name = "tardis.apps.shib_header_auth"
    verbose_name = "Shibboleth Header Auth"
