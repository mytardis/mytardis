from tardis.test_settings import *

DATABASES = {
    'default': {
        'ENGINE':   "django.db.backends.postgresql_psycopg2",
        'NAME':     "tardis",
        'USER':     "runner",
        'PASSWORD': "semaphoredb",
        'HOST':     "localhost",
        'PORT':     "",
    }
}
