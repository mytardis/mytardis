# pylint: disable=wildcard-import,unused-wildcard-import
from tardis.test_settings import *  # noqa # pylint: disable=W0401,W0614

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "mytardis",
        "USER": "root",
        "PASSWORD": "mysql",
        "HOST": "mysql",
        "PORT": "3306",
        "STORAGE_ENGINE": "InnoDB",
        "OPTIONS": {
            "init_command": "SET default_storage_engine=InnoDB",
            "charset": "utf8",
            "use_unicode": True,
        },
    },
}
