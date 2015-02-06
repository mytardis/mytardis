#!/bin/bash

sudo apt-get update
sudo apt-get install python-pip git libxml2-dev libxslt1-dev python-dev zlib1g-dev
sudo apt-get install python-virtualenv virtualenvwrapper python-psycopg2 python-yaml ipython python-wand
sudo apt-get install python-anyjson python-bs4 python-billiard python-feedparser python-html5lib
sudo apt-get install python-httplib2 python-pystache python-crypto libpython2.7-stdlib pylint

. virtualenvwrapper.sh
mkvirtualenv --system-site-packages mytardis
pip install -U pip
pip install -r requirements.txt

mkdir -p var/store
mkdir -p var/staging
mkdir -p var/oai


export DJANGO_SETTINGS_MODULE=tardis.settings_changeme
django-admin.py collectstatic
django-admin.py runserver

# build docs
# (cd docs; sphinx .)
