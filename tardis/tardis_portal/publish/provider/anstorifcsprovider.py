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
    
    def get_anzsrcfor_subjectcodes(self):
        codes = ['029904']
        # TODO: The experiment ANDS schema should allow the user to add their own codes,
        #  which should be appended here
        return codes

    def get_local_subjectcodes(self):
        codes = []
        # TODO: The experiment ANDS schema should allow the user to add their own
        #  local codes, which should be appended here
        return codes
    
    def get_rifcs_context(self, experiment):
        c = Context({})
        beamline = self.get_beamline(experiment)
        c['experiment'] = experiment
        c['originating_source'] = self.get_originating_source(beamline)
        c['email'] = self.get_email(beamline)
        c['beamline'] = self.get_beamline(experiment)
        c['key'] = self.get_key(experiment, beamline)
        c['sample_description_list'] = self.get_sample_description_list(experiment, beamline)
        c['investigator_list'] = self.get_investigator_list(experiment)
        c['produced_by'] = self.get_produced_by(beamline)
        c['license_title'] = self.get_license_title(experiment)
        c['license_uri'] = self.get_license_uri(experiment)
        return c