# pylint: disable=wildcard-import,unused-wildcard-import
from tardis.test_settings import *  # noqa # pylint: disable=W0401,W0614

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "mytardis",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "pg",
        "PORT": "5432",
    }
}
