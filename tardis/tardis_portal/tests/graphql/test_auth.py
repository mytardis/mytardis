import json

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model

from tardis.schema import schema


class userSignInTestCase(GraphQLTestCase):
    GRAPHQL_SCHEMA = schema

    def setUp(self):
        self.password = 'bobby*123!'
        self.user = get_user_model().objects.create_user(
            username='bob',
            password=self.password,
            email='bob@bobby.com.au',
            is_active=True
        )

    def tearDown(self):
        self.user.delete()

    def test_user_sign_in(self):
        rsp = self.query('''
            mutation userSignIn($input: UserSignInInput!) {
                userSignIn(input: $input) {
                    token
                    user {
                        username
                        email
                    }
                }
            }
            ''',
            op_name='userSignIn',
            input_data={
                'username': self.user.username,
                'password': self.password
            }
        )
        rsp = json.loads(rsp.content.decode('utf-8'))
        self.assertFalse('errors' in rsp)
        self.assertTrue('data' in rsp)
        self.assertTrue('userSignIn' in rsp['data'])
        data = rsp['data']['userSignIn']
        self.assertTrue('user' in data)
        self.assertTrue('username' in data['user'])
        self.assertTrue('email' in data['user'])
        self.assertEqual(data['user']['username'], self.user.username)
        self.assertEqual(data['user']['email'], self.user.email)
        self.assertTrue('token' in data)
