from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class DataFileResourceTests(APITestCase):
    def test_list_datafiles(self):
        """
        Ensure we can list datafiles.
        """
        url = reverse('datafile-list')
        # Firstly, test unauthenticated:
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
