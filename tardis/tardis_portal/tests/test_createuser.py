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

    def testInteractive(self):
        '''
        Just test that we can run
        ./manage.py createuser
        without any runtime exceptions by mocking the raw_input username and
        email entry
        '''

        def test_get_username(_):
            return 'testuser2'

        def test_get_email():
            return 'testuser2@example.com'

        def test_get_password(_):
            return 'Open Sesame!'

        call_command(
            'createuser', interactive=True, get_username=test_get_username,
            get_email=test_get_email, get_password=test_get_password)
