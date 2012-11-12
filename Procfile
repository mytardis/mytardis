uwsgi: ./run_uwsgi.sh --socket 127.0.0.1:$PORT
web: ./run_uwsgi.sh --http 127.0.0.1:8000
celerybeat: bin/django celerybeat
celeryd: bin/django celeryd --concurrency 1
