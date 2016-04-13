from tardis.test_settings import *

DATABASES = {
    'default': {
        'ENGINE':   "django.db.backends.postgresql_psycopg2",
        'NAME':     "tardis",
        'USER':     "mytardis",
        'PASSWORD': "password",
        'HOST':     "localhost",
        'PORT':     "5432",
    }
}
