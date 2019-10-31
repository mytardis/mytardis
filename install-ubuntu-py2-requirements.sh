# for Ubuntu 16.04 or 18.04
# sudo bash install-ubuntu-py2-requirements.sh

apt-get update
apt-get install git libldap2-dev libmagickwand-dev libsasl2-dev \
  libssl-dev libxml2-dev libxslt1-dev libmagic-dev curl gnupg \
  python-dev python-pip python-virtualenv virtualenvwrapper \
  zlib1g-dev libfreetype6-dev libjpeg-dev

curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -
sudo apt-get install -y nodejs
