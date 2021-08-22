Pull-Request Checklist
----------------------

MyTardis has been created by a very diverse group of contributors, all with
different backgrounds, aims and approaches. We also welcome your
contributions. However, to maintain viability of this project given its many
contributors, some basic coding standards need to be maintained.

If you're submitting a pull request, please run through this check-list first:

1. Is your code PEP-8 compliant? Please run pep8.py or equivalent to check.
2. Does your code lint cleanly? Install ``pylint`` and check with ``pylint --rcfile=.pylintrc tardis``
3. Have you merged or rebased your change against the current master?
4. Have you run the full suite of Python and JavaScript tests in a clean environment?

If you haven't::

  # Clean your environment
  unset PYTHON_SETTINGS_MODULE
  find . -name '*.py[co]' -delete
  # Clean install and full test
  python test.py
  python manage.py behave --settings=tardis.test_settings
  # Run test server
  python manage.py runserver

5. Does your change introduce new code? You should have tests covering it.
6. Does your change introduce new features? You should update the documentation in `docs/` accordingly.
7. After you send the pull request, Travis CI will automatically run some tests.
   Your pull request cannot be accepted until they pass.

If you have any questions, please contact us or submit an issue on github.
