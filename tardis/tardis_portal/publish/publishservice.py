
class PublishService():
    
    def __init__(self, providers, experiment):
        self.rc_providers = providers
        self.experiment = experiment
        self.provider = self._get_provider()
        
    def _get_provider(self):
        from django.utils.importlib import import_module  
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
            
            # Retrieve the provider that can deal with the experiment
            if provider and provider.is_schema_valid(self.experiment):
                return provider  
                     
        # return default provider
    
    def get_context(self):
        return self.provider.get_rifcs_context(self.experiment)
        
    def write_rifcs_to_oai_dir(self, oaipath):
        from tardis.tardis_portal.xmlwriter import XMLWriter
        subdir = self._get_subdir_path(oaipath)   
        xmlwriter = XMLWriter()
        xmlwriter.write_template_to_file(subdir, "experiment", 
                                         self.experiment.id, self.get_template(),
                                         self.get_context())    
    def _get_subdir_path(self, oaipath):
        import os
        subdir_name = str(self.experiment.id)
        path = os.path.join(oaipath, subdir_name)
        if not os.path.exists(path):
            os.mkdir(path)
        return subdir_name 
      
    def get_template(self):
        return self.provider.get_template(self.experiment)