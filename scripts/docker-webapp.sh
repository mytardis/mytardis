#!/bin/bash

./wait-for-db.sh

# Create database tables:
/appenv/bin/python mytardis.py migrate
/appenv/bin/python mytardis.py createcachetable default_cache
/appenv/bin/python mytardis.py createcachetable celery_lock_cache

# Copy static files (css, js etc):
/appenv/bin/python mytardis.py collectstatic --noinput

# Create demo superuser:
# SECURITY WARNING: Keep the password secret in production!
echo "from django.contrib.auth.models import User; \
    User.objects.create_superuser('${MYTARDIS_ADMIN_USERNAME}', \
    '${MYTARDIS_ADMIN_EMAIL}', '${MYTARDIS_ADMIN_PASSWORD}')" \
    | /appenv/bin/python mytardis.py shell

# Start gunicorn:
/appenv/bin/gunicorn -c /home/webapp/gunicorn_settings.py \
    -u webapp -g webapp -b unix:/tmp/gunicorn.socket -b 0.0.0.0:8000 \
    wsgi:application
