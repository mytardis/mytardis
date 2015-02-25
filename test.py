#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tardis.test_settings")

    from django.core.management import execute_from_command_line
    if len(sys.argv) < 2:
        execute_from_command_line(['./test.py', 'test'])
    else:
        execute_from_command_line(sys.argv)
