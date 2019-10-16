#!/bin/bash

echo This is a guide only, please either edit or run appropriate commands manually
exit

# for Ubuntu 16.04 or 18.04
# sudo bash install-ubuntu-py3-requirements.sh
# OR
# sudo bash install-ubuntu-py2-requirements.sh
# # optionally:
# # sudo apt-get install memcached python-memcache


# For macOS we need these dependencies installed via brew:
#
# brew install imagemagick@6
#   The Python Wand package is not yet compatible with ImageMagick 7.
#   If running MyTardis in your macOS environment is triggering
#   exceptions related to the Wand python package, please ensure that
#   your homebrew imagemagick is installed with compatible versions
#   of jpeg and libtiff by doing the following:
#
#   brew uninstall jpeg libtiff
#   brew install imagemagick@6
#   brew link --force imagemagick@6
#   echo "export MAGICK_HOME=/usr/local/opt/imagemagick@6/" >> ~/.bashrc
#   source ~/.bashrc
#
# brew install libmagic freetype
# brew install rabbitmq
# brew services start rabbitmq
#
# brew install postgresql # or SQLite may be sufficient for local development
#   or for a local development server, install http://postgresapp.com/

# For Ubuntu 18.04:
# source /etc/bash_completion.d/virtualenvwrapper

# For Ubuntu 16.04:
# source /usr/share/virtualenvwrapper/virtualenvwrapper.sh

# For macOS:
# source /usr/local/bin/virtualenvwrapper.sh

mkvirtualenv mytardis

pip install -U pip
pip install -r requirements.txt

# To install minimal Javascript dependencies for production:
npm install --production

# To install Javascript dependencies for production and for testing:
npm install && npm test

# Building the webpack bundle is not required to run the Python unit
# tests, but it is required to run the web application with
# manage.py runserver or with gunicorn:
npm run-script build

# Run the Python unit tests:
mkdir -p var/store
python test.py

# execute this wonderful command to have your settings.py created/updated
# with a generated Django SECRET_KEY (required for MyTardis to run)
python -c "import os; from random import choice; key_line = '%sSECRET_KEY=\"%s\"  # generated from build.sh\n' % ('from .default_settings import *  # pylint: disable=W0401,W0614\n\n' if not os.path.isfile('tardis/settings.py') else '', ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789@#%^&*(-_=+)') for i in range(50)])); f=open('tardis/settings.py', 'a+'); f.write(key_line); f.close()"

# for empty databases, sync all and fake migrate, otherwise run a real migration
python manage.py migrate
python manage.py createcachetable default_cache
python manage.py createcachetable celery_lock_cache
python manage.py collectstatic

python manage.py createsuperuser
python manage.py runserver
# os x:
open http://127.0.0.1:8000/
