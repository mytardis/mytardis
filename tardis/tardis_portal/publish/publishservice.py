
class PublishService():
    
    def __init__(self, providers, experiment):
        self.rc_providers = providers
        self.experiment = experiment
        self.provider = None
    
    def get_context(self):
        # get the appropriate provider
        from django.utils.importlib import import_module  
        provider = None
        c = None
        for pmodule in self.rc_providers:
            # Import the module
            try:
                module_name, klass_name = pmodule.rsplit('.', 1)
                module = import_module(module_name)
            except ImportError, e:
                # TODO Handle error
                raise e
            
            # Create the Instance
            try:            
                provider_class = getattr(module, klass_name)
                provider = provider_class()
            except AttributeError, e:
                # TODO Handle Error
                raise e  
            # Now get the correct schema (if any)
            if provider and provider.is_schema_valid(self.experiment):
                self.provider = provider
                return provider.get_rifcs_context(self.experiment)
        return None
        
    def get_template(self):
        return self.provider.get_template(self.experiment)
            
            

            