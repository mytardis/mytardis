from django.test import TestCase
from tardis.tardis_portal.models import User, Experiment
from tardis.tardis_portal.publish.provider.schemarifcsprovider import SchemaRifCsProvider
        
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
    

class PublishServiceTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='TestUser',
                                             email='user@test.com',
                                             password='secret')
        self.settings = ('tardis.tardis_portal.tests.test_publishservice.MockRifCsProvider',)
        self.e1 = Experiment(title="Experiment 1", created_by=self.user, public=False)
        self.e2 = Experiment(title="Experiment 2", created_by=self.user, public=True)
        
    def testInitialisation(self):
        from tardis.tardis_portal.publish.publishservice import PublishService
        service = PublishService(self.settings, self.e1)
        self.assertEquals(self.e1, service.experiment)
        self.assertTrue(isinstance(service.provider, MockRifCsProvider))
        
    def testContext(self):
        from tardis.tardis_portal.publish.publishservice import PublishService
        service = PublishService(self.settings, self.e1)
        c = service.get_context()
        self.assertEquals(c['experiment'], self.e1)
        self.assertEquals(c['beamline'], BEAMLINE_VALUE)
        self.assertEquals(c['sample_description_list'], SAMPLE_DESCS_VALUE)
        self.assertEquals(c['produced_by'], 'tardis.synchrotron.org.au/%s' % BEAMLINE_VALUE)
        self.assertEquals(c['license_title'], LICENSE_TITLE_VALUE)
        self.assertEquals(c['license_uri'], LICENSE_URL_VALUE)
        
        