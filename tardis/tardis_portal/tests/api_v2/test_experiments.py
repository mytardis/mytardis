from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ExperimentResourceTests(APITestCase):
    def test_list_experiments(self):
        """
        Ensure we can list experiments.
        """
        url = reverse('experiment-list')
        # Firstly, test unauthenticated:
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
