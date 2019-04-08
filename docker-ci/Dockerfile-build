FROM mytardis/mytardis-base

RUN apt-get update && apt-get install \
    -qy \
    build-essential \
    git \
    ipython \
    libfreetype6-dev \
    libjpeg-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    python-dev \
    zlib1g-dev \
    libmysqlclient-dev

ENV WHEELHOUSE=/wheelhouse
ENV PIP_WHEEL_DIR=/wheelhouse
ENV PIP_FIND_LINKS=/wheelhouse

RUN mkdir /wheelhouse
VOLUME /wheelhouse

WORKDIR /home/webapp

CMD . /appenv/bin/activate; \
    pip install -U setuptools; \
    pip wheel -r requirements.txt; \
    pip wheel -r requirements-postgres.txt; \
    pip wheel -r requirements-mysql.txt;
