from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class DatasetResourceTests(APITestCase):
    def test_list_datasets(self):
        """
        Ensure we can list datasets.
        """
        url = reverse('dataset-list')
        # Firstly, test unauthenticated:
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
