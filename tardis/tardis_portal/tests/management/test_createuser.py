from django.test import TestCase
from django.core.management import call_command


class CreateUserTestCase(TestCase):

    def testNoInput(self):
        '''
        Just test that we can run
        ./manage.py createuser --username testuser1 --email testuser1@example.com --noinput
        without any runtime exceptions
        '''
        call_command('createuser', username='testuser1', email='testuser1@example.com', interactive=False)
