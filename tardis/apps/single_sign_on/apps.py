from tardis.app_config import AbstractTardisAppConfig


class ShibbolethHeaderAuthConfig(AbstractTardisAppConfig):
    name = "tardis.apps.single_sign_on"
    verbose_name = "Single Sign On Auth"
