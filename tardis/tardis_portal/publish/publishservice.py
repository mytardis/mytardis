import os


class PublishService:
    def __init__(self, providers, experiment):
        self.rc_providers = providers
        self.experiment = experiment
        self.provider = self._get_provider()

    def _get_provider(self):
        from .provider.rifcsprovider import RifCsProvider

        if self.rc_providers:
            from importlib import import_module

            for pmodule in self.rc_providers:
                # Import the module
                try:
                    module_name, klass_name = pmodule.rsplit(".", 1)
                    module = import_module(module_name)
                except ImportError as e:
                    # TODO Show appropriate error msg
                    raise e

                # Create the Instance
                try:
                    provider_class = getattr(module, klass_name)
                    provider = provider_class()
                except AttributeError as e:
                    # TODO Show appropriate error msg
                    raise e

                # Retrieve the provider that can deal with the experiment
                if provider and provider.is_schema_valid(self.experiment):
                    return provider
        # Can't find a matching provider, return a default one
        return RifCsProvider()

    def get_context(self):
        return self.provider.get_rifcs_context(self.experiment)

    def manage_rifcs(self, oaipath):
        if self.provider.can_publish(self.experiment):
            self._write_rifcs_to_oai_dir(oaipath)
        else:
            self._remove_rifcs_from_oai_dir(oaipath)

    def _remove_rifcs_from_oai_dir(self, oaipath):
        filename = os.path.join(oaipath, "MyTARDIS-%s.xml" % self.experiment.id)
        if os.path.exists(filename):
            os.remove(filename)

    def _write_rifcs_to_oai_dir(self, oaipath):
        from ..xmlwriter import XMLWriter

        xmlwriter = XMLWriter()
        os.path.isdir(oaipath) or os.makedirs(oaipath)
        xmlwriter.write_template_to_dir(
            oaipath,
            "MyTARDIS-%s.xml" % self.experiment.id,
            self.get_template(),
            self.get_context(),
        )

    def get_template(self):
        return self.provider.get_template(self.experiment)
