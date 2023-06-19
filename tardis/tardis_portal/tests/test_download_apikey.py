# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from tastypie.test import ResourceTestCaseMixin


class ApiKeyDownloadTestCase(ResourceTestCaseMixin, TestCase):

    def setUp(self):
        # create a test user
        self.username = 'test'
        self.email = 'test@example.com'
        self.password = 'passw0rd'
        self.user = User.objects.create_user(username=self.username,
                                             email=self.email,
                                             password=self.password)

    def tearDown(self):
        self.user.delete()

    def test_download_apikey(self):
        download_api_key_url = reverse(
            'tardis.tardis_portal.download.download_api_key')
        client = Client()

        # Expect redirect to login
        response = client.get(download_api_key_url)
        self.assertEqual(response.status_code, 302)

        # Login as user
        login = client.login(username=self.username, password=self.password)
        self.assertTrue(login)
        response = client.get(download_api_key_url)
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="{0}.key"'.format(self.username))
        self.assertEqual(response.status_code, 200)
        response_content = b"".join(response.streaming_content).decode()
        self.assertEqual(response_content,
                         self.create_apikey(username=self.username,
                                            api_key=self.user.api_key.key))
