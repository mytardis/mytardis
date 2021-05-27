import os

from django.test import TestCase
from django.conf import settings

from ..models import User, Experiment
from ..publish.provider.rifcsprovider import RifCsProvider
from ..publish.publishservice import PublishService

BEAMLINE_VALUE = "myBeamline"
LICENSE_URL_VALUE = "http://some.uri.com"


class MockRifCsProvider(RifCsProvider):

    def is_schema_valid(self, experiment):
        return True

    def get_beamline(self, experiment):
        return BEAMLINE_VALUE

    def get_license_uri(self, experiment):
        return LICENSE_URL_VALUE

    def get_template(self, experiment):
        '''
        tardis.test_settings adds this to the template dirs:
        tardis/tardis_portal/tests/rifcs/
        '''
        return "default.xml"

    def get_rifcs_context(self, experiment):
        c = dict()
        c['experiment'] = experiment
        c['description'] = experiment.description
        c['beamline'] = self.get_beamline(experiment)
        c['license_url'] = self.get_license_uri(experiment)
        return c


class PublishServiceTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='TestUser',
                                             email='user@test.com',
                                             password='secret')
        self.settings = ('tardis.tardis_portal.tests.test_publishservice.MockRifCsProvider',)
        self.e1 = Experiment(id="1", title="Experiment 1",
                             description="This is my description.",
                             created_by=self.user,
                             public_access=Experiment.PUBLIC_ACCESS_NONE)

    def testInitialisation(self):
        service = PublishService(self.settings, self.e1)
        self.assertEqual(self.e1, service.experiment)
        self.assertTrue(isinstance(service.provider, MockRifCsProvider))

    def testInitialisationNoProvider(self):
        service = PublishService(None, self.e1)
        self.assertIsNone(service.rc_providers)
        from ..publish.provider.rifcsprovider import RifCsProvider
        self.assertTrue(isinstance(service.provider, RifCsProvider))
        self.assertFalse(isinstance(service.provider, MockRifCsProvider))

    def testContext(self):
        service = PublishService(self.settings, self.e1)
        c = service.get_context()
        self.assertEqual(c['experiment'], self.e1)
        self.assertEqual(c['beamline'], BEAMLINE_VALUE)
        self.assertEqual(c['license_url'], LICENSE_URL_VALUE)

    def testManageRifCsCreateAndRemove(self):
        service = PublishService(self.settings, self.e1)
        self.assertFalse(service.provider.can_publish(self.e1))
        service.manage_rifcs(settings.OAI_DOCS_PATH)
        rifcs_output_dir = os.path.join(settings.OAI_DOCS_PATH)
        rifcs_file = os.path.join(rifcs_output_dir, "MyTARDIS-1.xml")
        self.assertFalse(os.path.exists(rifcs_file))

        self.e1.public_access = Experiment.PUBLIC_ACCESS_FULL
        service.manage_rifcs(settings.OAI_DOCS_PATH)
        self.assertTrue(os.path.exists(rifcs_file))

        # Set to false again and see if it deletes it
        self.e1.public_access = Experiment.PUBLIC_ACCESS_NONE
        service.manage_rifcs(settings.OAI_DOCS_PATH)
        self.assertFalse(os.path.exists(rifcs_file))

    def testManageRifCsCheckContent(self):
        service = PublishService(self.settings, self.e1)
        self.e1.public_access = Experiment.PUBLIC_ACCESS_FULL
        service.manage_rifcs(settings.OAI_DOCS_PATH)
        rifcs_output_dir = os.path.join(settings.OAI_DOCS_PATH)
        rifcs_file = os.path.join(rifcs_output_dir, "MyTARDIS-1.xml")
        self.assertTrue(os.path.exists(rifcs_file))
        with open(rifcs_file) as output:
            lines = output.readlines()
        self.assertIn("experiment title: Experiment 1\n", lines)
        self.assertIn("experiment id: 1\n", lines)
        self.assertIn("experiment description: This is my description.\n", lines)
        self.assertIn("beamline: %s\n" % BEAMLINE_VALUE, lines)
        self.assertIn("license uri: %s\n" % LICENSE_URL_VALUE, lines)

        # Set to false again and see if it deletes it
        self.e1.public_access = Experiment.PUBLIC_ACCESS_NONE
        service.manage_rifcs(settings.OAI_DOCS_PATH)
        self.assertFalse(os.path.exists(rifcs_file))
