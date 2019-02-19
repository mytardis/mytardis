Dockerfiles for Continuous Integration
======================================

Setup
-----

The folowing command is run to create the ``mytardis-base`` image and
build the wheelhouse::

  docker-compose -f docker-ci/docker-build.yml run builder


Test
----

The following commands are run to perform the tests and report coverage::

  docker-compose -f docker-ci/docker-test.yml run -e TEST_TYPE=memory \
    -e CODACY_PROJECT_TOKEN=$CODACY_PROJECT_TOKEN \
    -e COVERALLS_REPO_TOKEN=$COVERALLS_REPO_TOKEN \
    -e CI_NAME=SemaphoreCI -e CI_BUILD_NUMBER=$SEMAPHORE_BUILD_NUMBER \
    -e CI_BRANCH=$BRANCH_NAME -e PULL_REQUEST_NUMBER=$PULL_REQUEST_NUMBER \
    test

  docker-compose -f docker-ci/docker-test.yml run -e TEST_TYPE=pg test

  docker-compose -f docker-ci/docker-test.yml run -e TEST_TYPE=behave test

  docker-compose -f docker-ci/docker-test.yml run -e TEST_TYPE=mysql test

  docker-compose -f docker-ci/docker-test.yml run -e TEST_TYPE=pylint test


Docker Hub
----------

The following command is run to push the resulting images to Docker Hub::

  for image in mytardis/mytardis-base mytardis/mytardis-run mytardis/mytardis-test; do if [ ! -v PULL_REQUEST_NUMBER ]; then if [ ! "$(git tag --points-at $BRANCH_NAME)" == "" ]; then tag=$(git tag --points-at $BRANCH_NAME); docker tag $image $image:$tag; docker push $image:$tag; elif [ "$BRANCH_NAME" == "master" ]; then docker push $image; elif [ "$BRANCH_NAME" == "develop" ]; then tag=develop; docker tag $image $image:$tag; docker push $image:$tag; fi; fi; done
