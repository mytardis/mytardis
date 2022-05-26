=====
Tests
=====

Running the Test Suite
----------------------
Run this command to run the unit tests::

    ./test.py (Macro Mode tests)
    ./test_micro.py (Micro Mode tests)

If you want to specify any options or specific tests to run, the test argument
is required first:

    ./test.py test --some-argument

You can choose to run the test suite with different options (e.g. with coverage,
with different verbosity, etc.). To see the full list of options, run the same
command with the --help flag.

Running Individual Unit Tests
-----------------------------

The unit tests reside in the ``tardis/tardis_portal/tests directory``.
To run the unit tests individually, you can use this command::

    ./test.py test <test_module_name_here>

Note that the test module name argument should be the relative file path with
"." as folder
separator. For example, if you want to run the test "test_authentication.py",
then your command to execute this test would be::

    ./test.py test tardis.tardis_portal.tests.test_authentication

Other options
-------------

You can choose to include different options when running the unit tests (e.g.
run in verbose mode, print out a traceback, etc.). Run the test or django test
command with --help flag to see the the full list of options::

    ./test.py test --help


Running BDD tests
-----------------

To run BDD (Behaviour Driven Development) tests with the default settings and
headless Chrome, download ChromeDriver from http://chromedriver.chromium.org/downloads
and make it available in your PATH (e.g. in /usr/local/bin/) and run::

    ./test.py behave


Running QUnit tests
-------------------

The QUnit tests reside in the ``js_tests/`` directory.

``package.json`` contains ``devDependencies`` required for running these tests.

Running ``npm install`` will install everything you need, whereas
``npm install --production`` will skip the ``devDependencies``.

You can run the QUnit tests with::

    npm test

Or by running a web server::

    python -m SimpleHTTPServer

and opening http://127.0.0.1:8000/js_tests/tests.html in your browser.
