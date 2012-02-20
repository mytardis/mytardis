from django.test import TestCase
from django.test.client import Client

class OaiTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def testEndpointExists(self):
        response = self.client.get('/apps/oaipmh/')
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        pass
