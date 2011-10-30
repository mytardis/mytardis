from django.template import Context 
from django.conf import settings
from tardis.tardis_portal.models import ExperimentParameter, ParameterName, Schema  

import schemarifcsprovider
    
class AnstoRifCsProvider(schemarifcsprovider.SchemaRifCsProvider):      
    
    def __init__(self):
        super(AnstoRifCsProvider, self).__init__()
        self.namespace = 'http://www.tardis.edu.au/schemas/ansto/experiment/2011/06/21'  
        self.sample_desc_schema_ns = 'http://www.tardis.edu.au/schemas/ansto/sample/2011/06/21'
      
    def get_email(self, beamline):
        return "%s@ansto.gov.au" % beamline
        
    def get_originating_source(self, beamline):
        return "http://mecat-test.nbi.ansto.gov.au:8080/oai/provider"
        
    def get_key(self, experiment, beamline):
        return "mecat-test.nbi.ansto.gov.au:8080/experiment/%s" % experiment.id
    
    def get_rifcs_context(self, experiment):
        c = Context({})
        beamline = self.get_beamline(experiment)
        c['originating_source'] = self.get_originating_source(beamline)
        c['experiment_name'] = experiment.title
        c['beamline_email'] = self.get_email(beamline)
        c['experiment_end_date'] = experiment.end_time
        c['beamline'] = self.get_beamline(experiment)
        c['key'] = self.get_key(experiment, beamline)
        c['identifier'] = self.get_key(experiment, beamline)
        c['sample_description_list'] = self.get_sample_description_list(experiment, beamline)
        c['investigator_list'] = self.get_investigator_list(experiment)
        c['institution'] = experiment.institution_name
        return c