from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class FacilityResourceTests(APITestCase):
    def test_list_facilities(self):
        """
        Ensure we can list facilities.
        """
        url = reverse('facility-list')
        # Firstly, test unauthenticated:
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        password = 'testpass'
        User.objects.create_superuser('superuser', 'super@test.com', password)
        self.client.login(username='superuser', password=password)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
