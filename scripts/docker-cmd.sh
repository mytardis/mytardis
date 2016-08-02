#!/bin/bash

./scripts/wait-for-db.sh
export DJANGO_SETTINGS_MODULE=tardis.env_settings
. /appenv/bin/activate

case "$1" in
    gunicorn)
        # Create database tables:
        python mytardis.py migrate
        python mytardis.py createcachetable default_cache
        python mytardis.py createcachetable celery_lock_cache

        # Copy static files (css, js etc):
        python mytardis.py collectstatic --noinput
        # Create demo superuser:
        # SECURITY WARNING: Keep the password secret in production!
        echo "from django.contrib.auth.models import User; \
            User.objects.create_superuser('${MYTARDIS_ADMIN_USERNAME}', \
            '${MYTARDIS_ADMIN_EMAIL}', '${MYTARDIS_ADMIN_PASSWORD}')" \
            | python mytardis.py shell

        # Start gunicorn:
        gunicorn -n mytardis_gunicorn -k gevent \
            --chdir /home/webapp \
            -u webapp -g webapp -b 0.0.0.0:8000 \
            wsgi:application

	    (( exit_status = exit_status || $? ))
        ;;
    celerybeat)
        python mytardis.py celerybeat
	    (( exit_status = exit_status || $? ))
        ;;
    celeryd)
        python mytardis.py celeryd -c 1 \
            -Q celery,default,low_priority_queue -n "allqueues.%%h" \
            --loglevel INFO
	    (( exit_status = exit_status || $? ))
        ;;
    sftpd)
        python mytardis.py sftpd  # may need -H
	    (( exit_status = exit_status || $? ))
        ;;
    *)
        ;;
esac

exit $exit_status



