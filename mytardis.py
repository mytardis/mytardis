#!/usr/bin/env python
from __future__ import print_function
import os
import sys

import coverage


def run():
    custom_settings = 'tardis.settings'
    custom_settings_file = custom_settings.replace('.', '/') + '.py'
    demo_settings = 'tardis.settings_changeme'
    if os.path.isfile(custom_settings_file):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", custom_settings)
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", demo_settings)
        print('Using demo settings in "tardis/default_settings.py",'
              ' please add your own settings file, '
              '"tardis/settings.py".')

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    from django.core.exceptions import ImproperlyConfigured
    try:
        is_testing = 'test' in sys.argv
        if is_testing:
            # https://github.com/django-nose/django-nose/issues/180#issuecomment-93371418
            # Without this, coverage reporting starts after many modules have
            # already been imported, so module-level code is excluded from
            # coverage reports:
            cov = coverage.coverage(source=['tardis'], omit=['*/tests/*'])
            cov.set_option('report:show_missing', True)
            cov.erase()
            cov.start()
        run()
        if is_testing:
            cov.stop()
            cov.save()
            cov.report()
    except ImproperlyConfigured as e:
        if 'SECRET_KEY' in e.message:
            print(r'''
# execute this wonderful command to have your settings.py created/updated
# with a generated Django SECRET_KEY (required for MyTardis to run)
python -c "import os; from random import choice; key_line = '%sSECRET_KEY=\"%s\"  # generated from build.sh\n' % ('from tardis.settings_changeme import * \n\n' if not os.path.isfile('tardis/settings.py') else '', ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789\\!@#$%^&*(-_=+)') for i in range(50)])); f=open('tardis/settings.py', 'a+'); f.write(key_line); f.close()"
''')
        else:
            raise
