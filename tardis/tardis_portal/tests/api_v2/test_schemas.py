from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SchemaResourceTests(APITestCase):
    def test_list_schemas(self):
        """
        Ensure we can list schemas.
        """
        url = reverse('schema-list')
        # Firstly, test unauthenticated (hidden schemas should be excluded):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
