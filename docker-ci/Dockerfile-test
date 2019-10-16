FROM mytardis/mytardis-run

USER root
RUN apt-get update && apt-get install \
    -qy \
    unzip \
    openjdk-8-jre-headless \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    wget \
    slapd ldap-utils
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
RUN apt-get update && apt-get install -qy google-chrome-stable
RUN wget -N http://chromedriver.storage.googleapis.com/2.40/chromedriver_linux64.zip -P ~/
RUN unzip ~/chromedriver_linux64.zip -d ~/
RUN mv -f ~/chromedriver /usr/local/bin/chromedriver
ENV PATH="/usr/local/bin:${PATH}"
RUN chmod 0755 /usr/local/bin/chromedriver

RUN chown -R webapp:webapp /home/webapp
USER webapp
RUN . /appenv/bin/activate; \
    pip install --no-index -f /wheelhouse -r requirements-postgres.txt
RUN . /appenv/bin/activate; \
    pip install --no-index -f /wheelhouse -r requirements-mysql.txt
RUN . /appenv/bin/activate; \
    pip install coveralls codacy-coverage
VOLUME /home/webapp/tardis
VOLUME /home/webapp/docs

RUN mkdir -p var/store

CMD bash -c '. /appenv/bin/activate; source ./test.sh'
