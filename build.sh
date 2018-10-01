#!/bin/bash

echo This is a guide only, please either edit or run appropriate commands manually
exit

# for Ubuntu 16.04 or 18.04
# sudo bash install-ubuntu-requirements.sh
# # optionally:
# # sudo apt-get install memcached python-memcache


# For macOS we need these dependencies installed via brew:
#
# brew install imagemagick@6
#   The Python Wand library is not yet compatible with ImageMagick 7.
#   If you have trouble running the tests requiring Wand, ensure that
#   your homebrew imagemagick is installed with compatible versions
#   of jpeg and libtiff by doing the following:
#
#   brew uninstall jpeg libtiff
#   brew install imagemagick@6
#   brew link --force imagemagick@6
#
# brew install libmagic freetype
#
# brew install postgresql # or SQLite may be sufficient for local development
#   or for a local development server, install http://postgresapp.com/
#
# If you want to test asynchronous processing locally on macOS, you'll need
# to install a broker such as RabbitMQ, which can be installed with:
#
#   brew install erlang --without-wxmac
#   brew install rabbitmq
#
# The erlang dependency would be pulled in automatically if you simply ran
# "brew install rabbimq", however installing erlang with wxmac can pull in
# a newer version of libtiff which is incompatible with ImageMagick 6 (see above)
# If you don't need to test asynchronous processing on macOS, you can just set
# CELERY_ALWAYS_EAGER = True in your tardis/settings.py, to run all tasks
# synchronously, so that you don't require a broker like RabbitMQ.

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

mkdir -p var/store

# execute this wonderful command to have your settings.py created/updated
# with a generated Django SECRET_KEY (required for MyTardis to run)
python -c "import os; from random import choice; key_line = '%sSECRET_KEY=\"%s\"  # generated from build.sh\n' % ('from .default_settings import * \n\n' if not os.path.isfile('tardis/settings.py') else '', ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789@#%^&*(-_=+)') for i in range(50)])); f=open('tardis/settings.py', 'a+'); f.write(key_line); f.close()"

python test.py
# for empty databases, sync all and fake migrate, otherwise run a real migration
python manage.py migrate
python manage.py createcachetable default_cache
python manage.py createcachetable celery_lock_cache
python manage.py collectstatic

python manage.py createsuperuser
python manage.py runserver
# os x:
open http://127.0.0.1:8000/
