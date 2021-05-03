from django.test import TestCase

from ..apps import HsmConfig


class HsmAppConfigTestCase(TestCase):
    def test_app_config(self):
        self.assertEqual(HsmConfig.name, 'tardis.apps.hsm')
