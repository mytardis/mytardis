#!/usr/bin/env python
from __future__ import print_function
import os
import sys

if __name__ == "__main__":
    custom_settings = 'tardis.settings'
    custom_settings_file = custom_settings.replace('.', '/') + '.py'
    demo_settings = 'tardis.settings_changeme'
    if os.path.isfile(custom_settings_file):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", custom_settings)
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", demo_settings)
        print('Using demo settings in "tardis/settings_changeme.py",'
              ' please add your own settings file, '
              '"tardis/settings.py".')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
