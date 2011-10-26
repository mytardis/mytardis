from django.template import Context
from django.conf import settings
from tardis.tardis_portal.models import ExperimentParameter, ParameterName, Schema

import rifcsprovider    
    
class SynchrotronRifCsProvider(rifcsprovider.RifCsProvider):
    
    def __init__(self):
        super(SynchrotronRifCsProvider, self).__init__()
        self.namespace = 'http://www.tardis.edu.au/schemas/as/experiment/2010/09/21'
        self.sample_desc_schema_ns = 'http://www.tardis.edu.au/schemas/as/sample/2011/01/24'
    
    def get_beamline_email(self, beamline):
        return "%s@synchrotron.gov.au" % beamline
    
    def get_originating_source(self, beamline):
        return "http://tardis.synchrotron.org.au/oai/provider"
        
    def get_key(self, experiment, beamline):
        return "tardis.synchrotron.org.au/experiment/view/%s" % experiment.id
    
    def get_template(self, experiment):
        beamline = self.get_beamline(experiment)
        filename = ""
        if beamline == 'IR':
            filename = "IR.xml"
        elif beamline == 'SAX':
            filename = "SAX.xml"
        else:
            filename = "default.xml"   
        return settings.RIFCS_TEMPLATE_DIR + filename
     
    def get_rifcs_context(self, experiment):
        c = Context({})
        beamline = self.get_beamline(experiment)
        c['originating_source'] = self.get_originating_source(beamline)
        c['experiment_name'] = experiment.title
        c['beamline_email'] = self.get_beamline_email(beamline)
        c['experiment_end_date'] = experiment.end_time
        c['beamline'] = self.get_beamline(experiment)
        c['key'] = self.get_key(experiment, beamline)
        c['identifier'] = self.get_key(experiment, beamline)
        c['sample_description_list'] = self.get_sample_description_list(experiment, beamline)
        c['investigator_list'] = self.get_investigator_list(experiment)
        c['institution'] = experiment.institution_name
        return c