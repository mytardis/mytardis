'''
Tests relating to tokens (temporary links) used by My Publications view
'''
import json

from django.contrib.auth.models import User
from django.test import RequestFactory
from django.test import TestCase
from django.test.client import Client

from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.token import Token

from tardis.tardis_portal.views.authorisation import (
    create_token,
    token_delete)

from ..models import Publication
from ..views import (
    retrieve_access_list_tokens_json,
    tokens)


class PublicationTokensTestCase(TestCase):
    def setUp(self):
        username = 'tardis_user1'
        pwd = 'secret'  # nosec
        email = ''
        self.user = User.objects.create_user(username, email, pwd)

        self.draft_pub1 = Publication.safe.create_draft_publication(
            self.user,
            'Test Publication Draft1',
            'Publication draft description1')

        self.test_token1 = Token(experiment=self.draft_pub1, user=self.user)
        self.test_token1.save_with_random_token()

        self.test_token2 = Token(experiment=self.draft_pub1, user=self.user)
        self.test_token2.save_with_random_token()

    def test_create_token(self):
        '''
        Test creating a temporary link for a draft publications
        '''
        factory = RequestFactory()
        request = factory.post(
            '/experiment/view/%s/create_token/' % self.draft_pub1.id)
        request.user = self.user
        token_count = Token.objects.filter(experiment=self.draft_pub1).count()
        response = create_token(request, experiment_id=self.draft_pub1.id)
        self.assertEqual(response.status_code, 200)
        expected = dict(success=True)
        self.assertEqual(
            json.loads(response.content), expected)
        self.assertEqual(
            Token.objects.filter(experiment=self.draft_pub1).count(),
            token_count + 1)

    def test_delete_token(self):
        '''
        Test deleting a temporary link for a draft publications
        '''
        token = Token(experiment=self.draft_pub1, user=self.user)
        token.save_with_random_token()
        factory = RequestFactory()
        request = factory.post('/token/delete/%s/' % token.id)
        request.user = self.user
        token_count = Token.objects.filter(experiment=self.draft_pub1).count()
        response = token_delete(request, token_id=token.id)
        self.assertEqual(response.status_code, 200)
        expected = dict(success=True)
        self.assertEqual(
            json.loads(response.content), expected)
        self.assertEqual(
            Token.objects.filter(experiment=self.draft_pub1).count(),
            token_count - 1)

    def test_retrieve_access_list_tokens_json(self):
        '''
        Test retrieving a JSON list of tokens
        '''
        factory = RequestFactory()
        request = factory.get(
            '/apps/publication-workflow/tokens_json/%s/' % self.draft_pub1.id)
        request.user = self.user
        response = retrieve_access_list_tokens_json(
            request, experiment_id=self.draft_pub1.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 2)
        self.assertEqual(
            json.loads(response.content)[0]['experiment_id'],
            self.draft_pub1.id)
        self.assertEqual(
            json.loads(response.content)[1]['experiment_id'],
            self.draft_pub1.id)

    def test_tokens_view(self):
        '''
        Test requesting tokens view, which would be displayed in a modal dialog
        when requested from the My Publications page
        '''
        factory = RequestFactory()
        request = factory.get(
            '/apps/publication-workflow/tokens/%s/' % self.draft_pub1.id)
        request.user = self.user
        response = tokens(request, experiment_id=self.draft_pub1.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'PublicationTokensController as pubTokensCtrl',
            response.content)
