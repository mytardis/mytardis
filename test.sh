#!/bin/bash

if [ -v EXTRA_REQS ]; then
    pip install $EXTRA_REQS
fi

# in memory
python test.py test $TEST_ARGS
(( exit_status = exit_status || $? ))

# on postgres
python test.py test --settings=tardis.test_on_postgresql_settings $TEST_ARGS
(( exit_status = exit_status || $? ))

# on mysql
python test.py test --settings=tardis.test_on_mysql_settings $TEST_ARGS
(( exit_status = exit_status || $? ))

pylint --rcfile .pylintrc tardis
(( exit_status = exit_status || $? ))

exit $exit_status
