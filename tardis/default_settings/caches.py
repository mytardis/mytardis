# A dictionary containing the settings for all caches to be used with
# Django. The CACHES setting must configure a default cache; any
# number of additional caches may also be specified.  Once the cache
# is set up, you'll need to add
# 'django.middleware.cache.UpdateCacheMiddleware' and
# 'django.middleware.cache.FetchFromCacheMiddleware'
# to your MIDDLEWARE setting

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "default_cache",
    },
    # # or use memcached
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    #     'LOCATION': '127.0.0.1:11211',
    # },
    "celery-locks": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "celery_lock_cache",
    },
}
"""
change the CACHES setting to memcached if you prefer. Requires additional
dependencies.
"""
