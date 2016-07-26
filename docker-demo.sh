#!/bin/bash

# Create containers, and leave them running in the background:

docker-compose up -d

docker-compose run webapp /home/webapp/wait-for-db.sh

# Create database tables:
docker-compose run webapp /appenv/bin/python mytardis.py migrate
docker-compose run webapp /appenv/bin/python mytardis.py createcachetable default_cache
docker-compose run webapp /appenv/bin/python mytardis.py createcachetable celery_lock_cache

# Copy static files (css, js etc):
docker-compose run webapp /appenv/bin/python mytardis.py collectstatic --noinput

echo
echo "Restarting web application service after collecting static content..."
docker-compose restart webapp

# echo
# echo "Restarting celery worker, because docker-compose up's initial attempt to run the worker probably failed,"
# echo "because we're currently using the Django message broker, so it depends on the migrations..."
# docker-compose restart celeryworker

echo
echo "Now, let's create a MyTardis superuser. (Press ^C to skip.)"
echo

docker-compose run --rm webapp /appenv/bin/python mytardis.py createsuperuser

echo
echo "Now you can access MyTardis at http://localhost:8080"
echo

echo "You can view logs with: docker-compose logs"
echo

echo "You can list running containers with: docker ps"
echo

echo If you want to run a shell inside the mytardis_webapp container,
echo you can do the following:
echo "  docker exec -i -t [container_id] /bin/bash"
echo

echo To bring down the services, you can run:
echo "  docker-compose down"
echo
