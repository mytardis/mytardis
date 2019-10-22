FROM ubuntu:18.04

RUN mkdir -p /home/webapp
RUN groupadd -r webapp && useradd -r -g webapp webapp

ENV DEBIAN_FRONTEND noninteractive
RUN echo 'APT::Get::Assume-Yes "true";' > /etc/apt/apt.conf.d/90assumeyes

RUN apt-get update && apt-get install \
    -qy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    curl \
    git \
    gnupg \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    python-pip \
    python-virtualenv \
    virtualenvwrapper \
    libmagic-dev \
    libmagickwand-dev \
    libmysqlclient20 \
    && apt-get clean

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get install -y nodejs

RUN mkdir /appenv
RUN chown -R webapp:webapp /appenv

RUN chown -R webapp:webapp /home/webapp
USER webapp
RUN virtualenv --system-site-packages /appenv
RUN . /appenv/bin/activate; pip install -U pip wheel
COPY . /home/webapp/
USER root
