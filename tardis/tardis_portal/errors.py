'''
Created on 02/09/2010

@author: gerson
'''


class UnsupportedSearchQueryTypeError(Exception):

    def __init__(self, msg):
        Exception.__init__(self, msg)


class SearchQueryTypeUnprovidedError(Exception):

    def __init__(self, msg):
        Exception.__init__(self, msg)


class ParameterChoicesFormatError(Exception):

    def __init__(self, msg):
        Exception.__init__(self, msg)
