==========
Unit Tests
==========

Running the Test Suite
----------------------

Assuming you have followed the instructions on :doc:`install` to install and 
configure MyTARDIS, simply run this command to run the unit tests::

    ./bin/test

You can choose to run the test suite with different options (e.g. with coverage,
with different verbosity, etc.). To see the full list of options, run the same
command with the --help flag.

Running Individual Unit Tests
-----------------------------

The unit tests reside in the ./tardis/tardis_portal/tests directory. 
To run the unit tests individually, you can use this command::

    ./bin/django test <test_file_name_here>
    
Note that the test file name argument should be the full path with "." as folder
separator. For example, if you want to run the test "test_authentication.py",
then your command to execute this test would be::

    ./bin/django test tardis.tardis_portal.tests.test_authentication
    
You can choose to include different options when running the unit tests (e.g. 
run in verbose mode, print out a traceback, etc.). Run the test with --help flag
to see the the full list of options.
