FROM ubuntu:18.04

ENV APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE DontWarn
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

ENV LANG C.UTF-8

RUN apt-get update -y

RUN apt-get install -y \
    sudo git libldap2-dev libmagickwand-dev libsasl2-dev \
    libssl-dev libxml2-dev libxslt1-dev libmagic-dev curl gnupg \
    python3-dev python3-pip python3-venv zlib1g-dev libfreetype6-dev libjpeg-dev

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get install -y nodejs

RUN pip3 install virtualenvwrapper

RUN groupadd -g 1001 ubuntu
RUN useradd -rm -d /home/ubuntu -s /bin/bash -g ubuntu -G sudo -u 1001 ubuntu
USER ubuntu
WORKDIR /home/ubuntu

RUN git clone -b develop git://github.com/mytardis/mytardis.git

ENV VIRTUAL_ENV=/home/ubuntu/mytardis/mytardis
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install -U pip setuptools

WORKDIR /home/ubuntu/mytardis

RUN pip install -U -r requirements.txt
RUN npm install --production
RUN npm run-script build

RUN echo "from .default_settings import *\n\
DEBUG = True\n\
SINGLE_SEARCH_ENABLED = True\n\
INSTALLED_APPS += 'django_elasticsearch_dsl',\n\
INSTALLED_APPS += 'tardis.apps.search',\n\
ELASTICSEARCH_DSL = {\n\
    'default': {\n\
        'hosts': 'host.docker.internal:9200'\n\
    }\n\
}\n\
DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'\n\
DATABASES['default']['NAME'] = 'tardis_db'\n" >> tardis/settings.py

RUN python -c "import os; from random import choice; key_line = '%sSECRET_KEY=\"%s\"\n' % ('from .default_settings import * \n\n' if not os.path.isfile('tardis/settings.py') else '', ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789@#%^&*(-_=+)') for i in range(50)])); f=open('tardis/settings.py', 'a+'); f.write(key_line); f.close()"
RUN python manage.py migrate
RUN python manage.py createcachetable default_cache
RUN python manage.py createcachetable celery_lock_cache

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
