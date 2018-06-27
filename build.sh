#!/bin/bash

echo This is a guide only, please either edit or run appropriate commands manually
exit

# for Ubuntu 14.04
# sudo bash install-ubuntu-requirements.sh
# # optionally:
# # sudo apt-get install memcached python-memcache


# for OS X we need these dependencies installed via brew
# brew install imagemagick --with-libtiff
# brew install libmagic freetype
# brew install postgresql
# or for a local development server, install http://postgresapp.com/

# for Ubuntu 14.04
# source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
# for OS X
# source /usr/local/bin/virtualenvwrapper.sh

mkvirtualenv mytardis

pip install -U pip
pip install -r requirements.txt
# for OS X, but might also need some brew requirements.
pip install -r requirements-osx.txt

npm install

mkdir -p var/store

# execute this wonderful command to have your settings.py created/updated
# with a generated Django SECRET_KEY (required for MyTardis to run)
python -c "import os; from random import choice; key_line = '%sSECRET_KEY=\"%s\"  # generated from build.sh\n' % ('from tardis.settings_changeme import * \n\n' if not os.path.isfile('tardis/settings.py') else '', ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])); f=open('tardis/settings.py', 'a+'); f.write(key_line); f.close()"

python test.py
# for empty databases, sync all and fake migrate, otherwise run a real migration
python manage.py migrate
python manage.py createcachetable default_cache
python manage.py createcachetable celery_lock_cache
python manage.py collectstatic

python manage.py runserver
# os x:
open http://127.0.0.1:8000/
