from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ParameterNameResourceTests(APITestCase):
    def test_list_parameternames(self):
        """
        Ensure we can list parameter names.
        """
        url = reverse('parametername-list')
        # Firstly, test unauthenticated (hidden schemas should be excluded):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
