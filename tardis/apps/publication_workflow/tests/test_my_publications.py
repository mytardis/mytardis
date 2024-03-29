'''
Tests relating to My Publications view
'''
import json

from django.contrib.auth.models import User
from django.test import RequestFactory
from django.test import TestCase

from ..models import Publication

from ..views import retrieve_draft_pubs_list
from ..views import retrieve_scheduled_pubs_list
from ..views import retrieve_released_pubs_list
from ..views import retrieve_retracted_pubs_list


class MyPublicationsTestCase(TestCase):
    def setUp(self):
        username = 'tardis_user1'
        pwd = 'secret'  # nosec
        email = ''
        self.user = User.objects.create_user(username, email, pwd)

        self.draft_pub1 = Publication.safe.create_draft_publication(
            self.user,
            'Test Publication Draft1',
            'Publication draft description1')

        self.draft_pub2 = Publication.safe.create_draft_publication(
            self.user,
            'Test Publication Draft2',
            'Publication draft description2')

    def test_retrieve_draft_pubs_list(self):
        '''
        Test retrieving list of draft publications
        '''
        factory = RequestFactory()
        request = factory.get('/apps/publication-workflow/retrieve_draft_pubs_list/')
        request.user = self.user
        response = retrieve_draft_pubs_list(request)
        self.assertEqual(response.status_code, 200)
        expected = [
            {
                "id": self.draft_pub1.id,
                "title": self.draft_pub1.title,
                "release_date": None,
                "description": self.draft_pub1.description,
                "doi": None
            },
	    {
                "id": self.draft_pub2.id,
                "title": self.draft_pub2.title,
                "release_date": None,
                "description": self.draft_pub2.description,
                "doi": None
            }
        ]
        self.assertEqual(
            sorted(json.loads(response.content), key=lambda k: k['id']),
            expected)

    def test_retrieve_scheduled_pubs_list(self):
        '''
        Test retrieving list of scheduled publications
        '''
        factory = RequestFactory()
        request = factory.get('/apps/publication-workflow/retrieve_scheduled_pubs_list/')
        request.user = self.user
        response = retrieve_scheduled_pubs_list(request)
        self.assertEqual(response.status_code, 200)
        expected = []
        self.assertEqual(
            sorted(json.loads(response.content), key=lambda k: k['id']),
            expected)

    def test_retrieve_released_pubs_list(self):
        '''
        Test retrieving list of released publications
        '''
        factory = RequestFactory()
        request = factory.get('/apps/publication-workflow/retrieve_released_pubs_list/')
        request.user = self.user
        response = retrieve_released_pubs_list(request)
        self.assertEqual(response.status_code, 200)
        expected = []
        self.assertEqual(
            sorted(json.loads(response.content), key=lambda k: k['id']),
            expected)

    def test_retrieve_retracted_pubs_list(self):
        '''
        Test retrieving list of retracted publications
        '''
        factory = RequestFactory()
        request = factory.get('/apps/publication-workflow/retrieve_retracted_pubs_list/')
        request.user = self.user
        response = retrieve_retracted_pubs_list(request)
        self.assertEqual(response.status_code, 200)
        expected = []
        self.assertEqual(
            sorted(json.loads(response.content), key=lambda k: k['id']),
            expected)
