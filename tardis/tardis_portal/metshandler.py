'''
A module to hold custom handlers for experiment/dataset/datafile schemas
that do not conform to the recommended key-value pair metadata format.

.. moduleauthor::  Gerson Galang <gerson.galang@versi.edu.au>
'''


def store_metadata_value(dict, key, value):
    """To support multiple parameter values the metadata dictionary stores a 
    list of values for each key.  This is a convenience routine used by the
    parser and writer to store parameter values."""
    lst = dict.get(key, None)
    if lst:
        lst.append(value)
    else:
        lst = [value]
        dict[key] = lst


class CustomHandler():

    def __init__(self):
        self.metadataDict = {}

    def resetMetadataDict(self):
        self.metadataDict = {}


class MxDatafileHandler(CustomHandler):

    def __init__(self):
        CustomHandler.__init__(self)
        self.inOscillationRange = False
        self.grabOscillationRangeStart = False
        self.grabOscillationRangeEnd = False
        self.parameterName = None

    def startElement(self, name, attrs):
        if name == 'oscillationRange':
            self.inOscillationRange = True
        elif name == 'start' and self.inOscillationRange:
            self.grabOscillationRangeStart = True
        elif name == 'end' and self.inOscillationRange:
            self.grabOscillationRangeEnd = True
        else:
            self.parameterName = name

    def endElement(self, name):
        if name == 'oscillationRange':
            self.inOscillationRange = False
        elif name == 'start' and self.inOscillationRange:
            self.grabOscillationRangeStart = False
        elif name == 'end' and self.inOscillationRange:
            self.grabOscillationRangeEnd = False
        elif name == self.parameterName:
            self.parameterName = None

    def characters(self, chars):
        if self.grabOscillationRangeStart:
            store_metadata_value(self.metadataDict, 
                                 'oscillationRange/start', chars)
        elif self.grabOscillationRangeEnd:
            store_metadata_value(self.metadataDict, 
                                 'oscillationRange/end', chars)
        else:
            store_metadata_value(self.metadataDict, 
                                 self.parameterName, chars)

# the list of custom handlers the metsparser will use
customHandlers = {
    'http://www.tardis.edu.au/schemas/trdDatafile/1': MxDatafileHandler(), }
