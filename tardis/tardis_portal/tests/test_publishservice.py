from django.test import TestCase
from django.template import Context
from django.conf import settings
from tardis.tardis_portal.models import User, Experiment
from tardis.tardis_portal.publish.provider.rifcsprovider import RifCsProvider
from tardis.tardis_portal.publish.publishservice import PublishService

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
        return "tardis/tardis_portal/tests/rifcs/default.xml"

    def get_rifcs_context(self, experiment):
        c = Context({})
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
        self.assertEquals(self.e1, service.experiment)
        self.assertTrue(isinstance(service.provider, MockRifCsProvider))

    def testInitialisationNoProvider(self):
        service = PublishService(None, self.e1)
        self.assertIsNone(service.rc_providers)
        from tardis.tardis_portal.publish.provider.rifcsprovider import RifCsProvider
        self.assertTrue(isinstance(service.provider, RifCsProvider))
        self.assertFalse(isinstance(service.provider, MockRifCsProvider))

    def testContext(self):
        service = PublishService(self.settings, self.e1)
        c = service.get_context()
        self.assertEquals(c['experiment'], self.e1)
        self.assertEquals(c['beamline'], BEAMLINE_VALUE)
        self.assertEquals(c['license_url'], LICENSE_URL_VALUE)

    def testManageRifCsCreateAndRemove(self):
        service = PublishService(self.settings, self.e1)
        self.assertFalse(service.provider.can_publish(self.e1))
        import os
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
        import os
        rifcs_output_dir = os.path.join(settings.OAI_DOCS_PATH)
        rifcs_file = os.path.join(rifcs_output_dir, "MyTARDIS-1.xml")
        self.assertTrue(os.path.exists(rifcs_file))
        output = open(rifcs_file)
        lines = output.readlines()
        self.assertTrue("experiment title: Experiment 1\n" in lines)
        self.assertTrue("experiment id: 1\n" in lines)
        self.assertTrue("experiment description: This is my description.\n" in lines)
        self.assertTrue("beamline: %s\n" % BEAMLINE_VALUE in lines)
        self.assertTrue("license uri: %s\n" % LICENSE_URL_VALUE in lines)

        # Set to false again and see if it deletes it
        self.e1.public_access = Experiment.PUBLIC_ACCESS_NONE
        service.manage_rifcs(settings.OAI_DOCS_PATH)
        self.assertFalse(os.path.exists(rifcs_file))



