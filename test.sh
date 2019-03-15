#!/bin/bash

if [ -v EXTRA_REQS ]; then
    pip install $EXTRA_REQS
fi

# select test to run with TEST_TYPE, memory pg mysql pylint

function run_test {
    python test.py test --settings=$1
    result=$?
    if [ "$TEST_TYPE" == "memory" ]; then
	if [ -n "$PULL_REQUEST_NUMBER" ]; then
	    export TRAVIS_PULL_REQUEST=$PULL_REQUEST_NUMBER;
	else export TRAVIS_PULL_REQUEST='false'; fi
	if [ -v COVERALLS_REPO_TOKEN ]; then
	    coveralls
	fi
	if [ -v CODACY_PROJECT_TOKEN ]; then
	    coverage xml
	    python-codacy-coverage -r coverage.xml
	fi
    fi
    return $result
}

case "$TEST_TYPE" in
    memory)
	run_test tardis.test_settings
	(( exit_status = exit_status || $? ))
    ;;
    pg)
	run_test tardis.test_on_postgresql_settings
	(( exit_status = exit_status || $? ))
    ;;
    mysql)
	run_test tardis.test_on_mysql_settings
	(( exit_status = exit_status || $? ))
    ;;
    pylint)
	pylint --rcfile .pylintrc tardis
	(( exit_status = exit_status || $? ))
    ;;
    behave)
        npm install && npm test \
        && python test.py behave
	(( exit_status = exit_status || $? ))
    ;;
    *)
	run_test tardis.test_settings
	(( exit_status = exit_status || $? ))
	run_test tardis.test_on_postgresql_settings
	(( exit_status = exit_status || $? ))
	run_test tardis.test_on_mysql_settings
	(( exit_status = exit_status || $? ))
	pylint --rcfile .pylintrc tardis
	(( exit_status = exit_status || $? ))
    ;;
esac

exit $exit_status
