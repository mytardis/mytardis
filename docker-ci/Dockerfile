FROM python:3.6

RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -qy google-chrome-stable

RUN export CHROME_DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -N https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip -P ~/ && \
    unzip ~/chromedriver_linux64.zip -d ~/ && \
    mv -f ~/chromedriver /usr/local/bin/chromedriver && \
    chmod 0755 /usr/local/bin/chromedriver

RUN apt-get update && apt-get install -qy \
    libssl-dev \
    libsasl2-dev \
    libldap2-dev \
    libxi6 \
    libxss1

WORKDIR /app
COPY . /app

RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements-postgres.txt
RUN pip3 install -r requirements-mysql.txt

RUN mkdir -p var/store

CMD /app/test.sh
