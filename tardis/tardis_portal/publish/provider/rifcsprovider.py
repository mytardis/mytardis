from tardis.tardis_portal.models import ExperimentParameter, Schema

class RifCsProvider(object):
    
    def __init__(self):
        self.namespace = None
        self.schema = None
        
    def is_schema_valid(self, experiment):
        ep = ExperimentParameter.objects.filter(
                                    parameterset__experiment = experiment, 
                                    name__schema__namespace = self.namespace)
        if len(ep) > 0:
            self.schema = Schema.objects.get(namespace = self.namespace)
            return True
        return False
    
    def get_rifcs_context(self):
        return None