from django.test import TestCase
from tardis.tardis_portal.models import User, Experiment
from tardis.tardis_portal.publish.provider.schemarifcsprovider import SchemaRifCsProvider
from tardis.tardis_portal.publish.publishservice import PublishService
        
BEAMLINE_VALUE = "myBeamline"
SAMPLE_DESCS_VALUE = "sampleA\nsampleB\nsampleC\nsampleD\n"    
LICENSE_URL_VALUE = "http://some.uri.com"
LICENSE_TITLE_VALUE = "myLicense"   
        
class MockRifCsProvider(SchemaRifCsProvider):
    
    def is_schema_valid(self, experiment):
        return True
    
    def get_beamline(self, experiment):
        return BEAMLINE_VALUE
    
    def get_sample_description_list(self, experiment, beamline):
        return SAMPLE_DESCS_VALUE
    
    def get_license_uri(self, experiment):
        return LICENSE_URL_VALUE
    
    def get_license_title(self, experiment):
        return LICENSE_TITLE_VALUE
    
    def get_template(self, experiment):
        return "tardis/tardis_portal/rifcs/default.xml"

class PublishServiceTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='TestUser',
                                             email='user@test.com',
                                             password='secret')
        self.settings = ('tardis.tardis_portal.tests.test_publishservice.MockRifCsProvider',)
        self.e1 = Experiment(id="1", title="Experiment 1", created_by=self.user, public=False)
        
    def testInitialisation(self):
        service = PublishService(self.settings, self.e1)
        self.assertEquals(self.e1, service.experiment)
        self.assertTrue(isinstance(service.provider, MockRifCsProvider))
        
    def testContext(self):
        service = PublishService(self.settings, self.e1)
        c = service.get_context()
        self.assertEquals(c['experiment'], self.e1)
        self.assertEquals(c['beamline'], BEAMLINE_VALUE)
        self.assertEquals(c['sample_description_list'], SAMPLE_DESCS_VALUE)
        self.assertEquals(c['license_title'], LICENSE_TITLE_VALUE)
        self.assertEquals(c['license_uri'], LICENSE_URL_VALUE)     
        
    def testManageRifCs(self):
        service = PublishService(self.settings, self.e1)
        self.assertFalse(service.provider.can_publish(self.e1))
        import os
        test_oai_path = os.path.join("tardis/tardis_portal/tests", "rifcs")
        rifcs_output_dir = os.path.join(test_oai_path, self.e1.id)
        service.manage_rifcs(test_oai_path)
        self.assertFalse(os.path.exists(rifcs_output_dir))
        
        self.e1.public = True
        self.assertRaises(AttributeError, service.manage_rifcs, test_oai_path)
        self.assertTrue(os.path.exists(rifcs_output_dir))
    
        # Set to false again and see if it deletes it
        self.e1.public = False
        service.manage_rifcs(test_oai_path)
        self.assertFalse(os.path.exists(rifcs_output_dir))
        
    
        
        