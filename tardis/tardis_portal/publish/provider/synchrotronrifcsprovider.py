from tardis.tardis_portal.models import ExperimentParameter, ParameterName, Schema
from django.template import Context
import rifcsprovider    
    
class SynchrotronRifCsProvider(rifcsprovider.RifCsProvider):
    
    def __init__(self):
        super(SynchrotronRifCsProvider, self).__init__()
        self.namespace = 'http://www.tardis.edu.au/schemas/as/experiment/2010/09/21'
    
    def get_beamline_email(self, beamline):
        return "%s@synchrotron.gov.au" % beamline
        
    def get_beamline(self, experiment):    
        sch = Schema.objects.get(namespace=self.namespace)         
        param = ParameterName.objects.get(schema=sch, name='beamline')
        res = ExperimentParameter.objects.get(parameterset__experiment = experiment, name=param)
        return res.string_value
    
    def get_originating_source(self, beamline):
        return "http://tardis.synchrotron.org.au/oai/provider"
        
    def get_key(self, experiment, beamline):
        return "tardis.synchrotron.org.au/experiment/%s" % experiment.id
        
    def get_institution(self, experiment):
        return experiment.institution
    
    def get_sample_description_list(self, experiment, beamline):
        return "blah\nblah\nblah"
    
    def get_investigator_list(self, experiment):
        return "*me\n*me\n*me"
    
    def get_rifcs_context(self, experiment):
        c = Context({})
        beamline = self.get_beamline(experiment)
        c['originating_source'] = self.get_originating_source(beamline)
        c['experiment_name'] = experiment.title
        c['beamline_email'] = self.get_beamline_email(beamline)
        c['experiment_end_date'] = experiment.end_time
        c['beamline'] = self.get_beamline(experiment)
        #c['institution'] = self.get_institution(beamline)
        c['key'] = self.get_key(experiment, beamline)
        c['identifier'] = self.get_key(experiment, beamline)
        c['sample_description_list'] = self.get_sample_description_list(experiment, beamline)
        c['investigator_list'] = self.get_investigator_list(experiment)
        return c