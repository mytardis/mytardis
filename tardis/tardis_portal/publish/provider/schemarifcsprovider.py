from tardis.tardis_portal.models import ExperimentParameter, ExperimentParameterSet, ParameterName, Schema
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
from django.template import Context

import rifcsprovider

class SchemaRifCsProvider(rifcsprovider.RifCsProvider):
    
    def __init__(self):
        self.namespace = None
        self.sample_desc_schema_ns = None
        self.creative_commons_schema_ns = 'http://www.tardis.edu.au/schemas/creative_commons/2011/05/17'
        
    def is_schema_valid(self, experiment):
        eps = ExperimentParameter.objects.filter(
                                    parameterset__experiment = experiment, 
                                    name__schema__namespace = self.namespace)
        if len(eps) > 0:
            schema = Schema.objects.get(namespace = self.namespace)
            return True
        return False
            
    def get_beamline(self, experiment):    
        sch = Schema.objects.get(namespace=self.namespace)         
        param = ParameterName.objects.get(schema=sch, name='beamline')
        res = ExperimentParameter.objects.get(parameterset__experiment = experiment, name=param)
        return res.string_value
         
    def get_produced_by(self, beamline):
        return 'tardis.synchrotron.org.au/%s' % beamline
   
    def get_investigator_list(self, experiment):
        authors = [a.author for a in experiment.author_experiment_set.all()]
        return "\n*".join(authors)
           
    def get_sample_description_list(self, experiment, beamline):
        sch = Schema.objects.get(namespace=self.sample_desc_schema_ns)
        params = ParameterName.objects.get(schema=sch, name='SampleDescription')
        descriptions = [x.string_value for x in 
                         ExperimentParameter.objects.filter(
                          parameterset__experiment=experiment, name=params)]
        return "\n".join(descriptions)
    
    def get_license_uri(self, experiment):
        parameterset = ExperimentParameterSet.objects.filter(
                            schema__namespace=self.creative_commons_schema_ns,
                            experiment__id=experiment.id)
        if len(parameterset) > 0:
            psm = ParameterSetManager(parameterset=parameterset[0])
            return psm.get_param("license_uri", True)
        return None
    
    def get_license_title(self, experiment):
        parameterset = ExperimentParameterSet.objects.filter(
                            schema__namespace=self.creative_commons_schema_ns,
                            experiment__id=experiment.id)
        if len(parameterset) > 0:
            psm = ParameterSetManager(parameterset=parameterset[0])
            return psm.get_param("license_name", True)
        return None
    
    def get_rifcs_context(self, experiment):
        c = Context({})
        beamline = self.get_beamline(experiment)
        c['experiment'] = experiment
        c['beamline'] = self.get_beamline(experiment)
        c['sample_description_list'] = self.get_sample_description_list(experiment, beamline)
        c['investigator_list'] = self.get_investigator_list(experiment)
        c['produced_by'] = self.get_produced_by(beamline)
        c['license_title'] = self.get_license_title(experiment)
        c['license_uri'] = self.get_license_uri(experiment)
        return c