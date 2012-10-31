class MigrationError(Exception):
    pass

class MigrationProviderError(MigrationError):
    pass

class TransferProvider(object):
    def __init__(self, name):
        self.name = name
