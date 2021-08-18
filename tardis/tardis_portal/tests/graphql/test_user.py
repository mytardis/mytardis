from graphql_jwt.testcases import JSONWebTokenTestCase
from django.contrib.auth import get_user_model


class userSignInTestCase(JSONWebTokenTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='bob',
            password='bobby*312',
            email='bob@bobby.com.au',
            is_active=True
        )

    def tearDown(self):
        self.user.delete()

    def test_user_not_autenticated(self):
        query = '''
        {
            user {
                username
            }
        }
        '''
        rsp = self.client.execute(query).to_dict()
        self.assertFalse('errors' in rsp)
        self.assertTrue('data' in rsp)
        data = rsp['data']
        self.assertTrue('user' in data)
        self.assertEqual(data['user'], None)

    def test_user_autenticated(self):
        query = '''
        {
            user {
                username
                email
            }
        }
        '''
        self.client.authenticate(self.user)
        rsp = self.client.execute(query).to_dict()
        self.client.logout()
        self.assertFalse('errors' in rsp)
        self.assertTrue('data' in rsp)
        data = rsp['data']
        self.assertTrue('user' in data)
        self.assertTrue('username' in data['user'])
        self.assertTrue('email' in data['user'])
        self.assertEqual(data['user']['username'], self.user.username)
        self.assertEqual(data['user']['email'], self.user.email)
