#!/usr/bin/env python
import os
import sys

import coverage


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tardis.test_settings_microacls")

    from django.core.management import execute_from_command_line

    # https://github.com/django-nose/django-nose/issues/180#issuecomment-93371418
    # Without this, coverage reporting starts after many modules have
    # already been imported, so module-level code is excluded from
    # coverage reports:
    cov = coverage.coverage(source=["tardis"], omit=["*/tests/*"])
    cov.set_option("report:show_missing", True)
    if len(sys.argv) > 1 and sys.argv[1] == "behave":
        cov.set_option("run:plugins", ["django_coverage_plugin"])
        cov.set_option("report:include", ["*.html", "*.js"])
    cov.load()
    cov.start()

    if len(sys.argv) < 2:
        execute_from_command_line(["./test.py", "test"])

    else:
        execute_from_command_line(sys.argv)

    cov.stop()
    cov.save()
    cov.report()
