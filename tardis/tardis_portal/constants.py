'''
constants.py

@author: Gerson Galang
'''

DATAFILE_RESULTS_PER_PAGE = 25

FORM_RANGE_HIGHEST_NUM = 9999999999

FORM_RANGE_LOWEST_NUM = 0

RANDOM_PASSWORD_LENGTH = 8

SCHEMA_DICT = {
    'mx':
        {'datafile': 'http://www.tardis.edu.au/schemas/trdDatafile/1',
        'dataset': 'http://www.tardis.edu.au/schemas/trdDataset/2'},
    'saxs':
        {'datafile':
         'http://www.tardis.edu.au/schemas/saxs/datafile/2010/08/10',
        'dataset': 'http://www.tardis.edu.au/schemas/saxs/dataset/2010/08/10'},
    'ir':
        {'datafile': 'http://www.tardis.edu.au/schemas/opusDatafile/1',
         'dataset': 'http://www.tardis.edu.au/schemas/opusDataset/1'},
    }

EXPERIMENT_SCHEMAS = \
    ['http://www.tardis.edu.au/schemas/as/experiment/2010/09/21',
     'http://www.tardis.edu.au/schemas/as/sample/2011/01/24',
]
