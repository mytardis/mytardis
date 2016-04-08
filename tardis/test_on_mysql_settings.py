from tardis.test_settings import *

DATABASES = {
    'default': {
        'ENGINE':   "django.db.backends.mysql",
        'NAME':     "tardis",
        'USER':     "mytardis",
        'PASSWORD': "password",
        'HOST':     "localhost",
        'PORT':     "3306",
        'STORAGE_ENGINE':   "InnoDB",
        'OPTIONS': {
            'init_command': 'SET storage_engine=InnoDB',
            'charset':      'utf8',
            'use_unicode':  True,
        },
    }
}

