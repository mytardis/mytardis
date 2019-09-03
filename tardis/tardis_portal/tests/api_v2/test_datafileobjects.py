from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class DataFileObjectResourceTests(APITestCase):
    def test_list_datafileobjects(self):
        """
        Ensure we can list datafile objects.
        """
        url = reverse('datafileobject-list')
        # Firstly, test unauthenticated:
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
