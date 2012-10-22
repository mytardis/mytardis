==========
Unit Tests
==========

Before you can run unit tests, you have to configure ./bin/test to use test 
settings rather than normal settings.

Configure to use Test Settings
------------------------------

Assuming you have followed the instructions on :doc:`install` to install and 
configure MyTARDIS, the last line of ./bin/test file to the following::

    djangorecipe.test.main('tardis.settings', 'tardis')

Change this line to use 'tardis.test_settings' instead::

    djangorecipe.test.main('tardis.test_settings', 'tardis')


Running the Test Suite
----------------------

Run this command to run the unit tests::

    ./bin/test

You can choose to run the test suite with different options (e.g. with coverage,
with different verbosity, etc.). To see the full list of options, run the same
command with the --help flag.

Running Individual Unit Tests
-----------------------------

The unit tests reside in the ./tardis/tardis_portal/tests directory. 
To run the unit tests individually, you can use this command::

    ./bin/django test --settings=tardis.test_settings <test_file_name_here>
    
Note that the test file name argument should be the full path with "." as folder
separator. For example, if you want to run the test "test_authentication.py",
then your command to execute this test would be::

    ./bin/django test --settings=tardis.test_settings \
                      tardis.tardis_portal.tests.test_authentication
    
You can choose to include different options when running the unit tests (e.g. 
run in verbose mode, print out a traceback, etc.). Run the test or django test
command with --help flag to see the the full list of options::

    ./bin/django test --settings=tardis.test_settings --help

    
