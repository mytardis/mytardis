from tardis.tardis_portal.models import ExperimentParameter, ParameterName, Schema

class RifCsProvider(object):
    
    def __init__(self):
        self.namespace = None
        self.sample_desc_schema_ns = None
        
    def is_schema_valid(self, experiment):
        ep = ExperimentParameter.objects.filter(
                                    parameterset__experiment = experiment, 
                                    name__schema__namespace = self.namespace)
        if len(ep) > 0:
            schema = Schema.objects.get(namespace = self.namespace)
            return True
        return False
            
    def get_beamline(self, experiment):    
        sch = Schema.objects.get(namespace=self.namespace)         
        param = ParameterName.objects.get(schema=sch, name='beamline')
        res = ExperimentParameter.objects.get(parameterset__experiment = experiment, name=param)
        return res.string_value
    
    def get_rifcs_context(self):
        raise Exception(NotImplemented())
    
    def get_template(self, experiment):
        return "default.xml"
        
    def get_investigator_list(self, experiment):
        authors = [a.author for a in experiment.author_experiment_set.all()]
        return "\n".join(authors)
           
    def get_sample_description_list(self, experiment, beamline):
        sch = Schema.objects.get(namespace=self.sample_desc_schema_ns)
        params = ParameterName.objects.get(schema=sch, name='SampleDescription')
        descriptions = [x.string_value for x in 
                         ExperimentParameter.objects.filter(
                          parameterset__experiment=experiment, name=params)]
        return "\n".join(descriptions)