'''
A module which holds the METS structure objects. The objects here are
lightweight as they only keep metadata keys (IDs) instead of the actual
metadata values.

.. moduleauthor::  Gerson Galang <gerson.galang@versi.edu.au>
'''

from tardis.tardis_portal.logger import logger


class Experiment():

    def __init__(self, id, metadataIds):
        self.id = id
        self.metadataIds = metadataIds
        self.datasets = []
        self.authors = []
        self.title = None
        self.description = None
        self.institution = None
        self.url = None

    def __str__(self):
        returnStr = 'Experiment\n' + \
               '   - id: ' + toString(self.id) + '\n' + \
               '   - metadataId: ' + toString(self.metadataId) + '\n\n\n' + \
               'Datasets...\n'
        for ds in self.datasets:
            returnStr += str(ds)
        return returnStr + '\n'


class Dataset():

    def __init__(self, id, metadataIds):
        self.id = id
        self.metadataIds = metadataIds
        self.datafiles = []
        self.experiment = None
        self.title = None

    def __str__(self):
        returnStr = 'Dataset\n' + \
               '   - id: ' + toString(self.id) + '\n' + \
               '   - metadataId: ' + toString(self.metadataId) + '\n' + \
               '   - experimentId: ' + toString(
               self.experiment.id) + '\n\n' + \
               'Datafiles...\n'
        for df in self.datafiles:
            returnStr += str(df)
        return returnStr + '\n'


class Datafile():

    def __init__(self, id, name, size, metadataIds):
        self.id = id
        self.name = name
        self.size = size
        self.metadataIds = metadataIds
        self.url = None
        self.dataset = None

    def __str__(self):
        return 'Datafile\n' + \
               '   - id: ' + toString(self.id) + '\n' + \
               '   - name: ' + toString(self.name) + '\n' + \
               '   - size: ' + toString(self.size) + '\n' + \
               '   - metadataIds: ' + toString(self.metadataIds) + '\n' + \
               '   - datasetId: ' + toString(self.dataset.id) + '\n'


def toString(toBeConverted):
    '''Get the string representation of the object to be converted into string.
    This will also return 'None' as the string if the object of 'None' type.

    '''

    return toBeConverted is not None and str(toBeConverted) or 'None'
