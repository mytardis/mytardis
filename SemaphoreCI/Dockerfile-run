FROM mytardis/mytardis-base

# prebuilt wheels from django-build.yml
ADD wheelhouse /wheelhouse

USER webapp

WORKDIR /home/webapp

ENV DOCKER_BUILD true
RUN . /appenv/bin/activate; \
    pip install --no-index -f /wheelhouse -r requirements.txt
