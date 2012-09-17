Pull-Request Checklist
----------------------

If you're submitting a pull request, please run through this check-list first:

1. Have you merged or rebased your change against the current master?
2. Have you run the full suite of Python and JavaScript tests in a clean environment? 

If you haven't::

  # Clean your environment
  unset PYTHON_SETTINGS_MODULE
  find . -name '*.py[co]' -delete
  python bootstrap.py
  # Clean install and full test
  bin/buildout install && bin/django test --no-skip
  # Run test server then check Jasmine tests @ http://localhost:8000/jasmine/
  bin/django testserver

3. Does your change introduce new code? You should have tests covering it.
4. Does your change introduce new features? You should update the documentation in `docs/` accordingly.