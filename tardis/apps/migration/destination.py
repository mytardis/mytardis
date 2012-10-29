from django.conf import settings

from tardis.apps.migration import MigrationError

class Destination:
    def __init__(self, name):
        descriptor = None
        if len(settings.MIGRATION_DESTINATIONS) == 0:
            raise MigrationError("No destinations have been configured")
        for d in settings.MIGRATION_DESTINATIONS:
            if d['name'] == name:
                descriptor = d
        if not descriptor:
            raise ValueError('Unknown destination %s' % name)
        self.name = descriptor['name']
        self.base_url = descriptor['base_url']
        self.trust_length = descriptor.get('trust_length', False)
        self.datafile_protocol = descriptor.get('datafile_protocol', '')
        self.metadata_supported = descriptor.get('metadata_supported', False)
        # FIXME - is there a better way to do this?
        exec 'import tardis\n' + \
            'self.provider = ' + \
            settings.MIGRATION_PROVIDERS[descriptor['transfer_type']] + \
                '(self.name, self.base_url, ' + \
                'metadata_supported=self.metadata_supported)'
