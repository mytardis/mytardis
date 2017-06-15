apt-get -y update
apt-get -y install git ipython libldap2-dev libsasl2-dev \
  libssl-dev libxml2-dev libxslt1-dev python-anyjson \
  python-billiard python-bs4 python-crypto python-dateutil \
  python-dev python-flexmock python-html5lib \
  python-pip python-psycopg2 python-pystache \
  python-virtualenv python-wand python-yaml virtualenvwrapper \
  zlib1g-dev libfreetype6-dev libjpeg-dev
if [ $? -eq 0 ]; then
    touch /root/install-ubuntu-requirements-successful
fi
