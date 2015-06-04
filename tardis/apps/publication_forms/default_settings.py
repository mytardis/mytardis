'''
default settings for publication app
override in main settings
'''

PUBLICATION_NOTIFICATION_SENDER_EMAIL = 'emailsender@mytardisserver'
PUBLICATION_OWNER_GROUP = 'publication-admin'
PUBLICATION_SCHEMA_ROOT = 'http://www.tardis.edu.au/schemas/publication/'

# This schema holds bibliographic details including authors and
# acknowledgements
PUBLICATION_DETAILS_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'details/'

# Any experiment with this schema is treated as a draft publication
# This schema will be created automatically if not present
PUBLICATION_DRAFT_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'draft/'

# Form mappings
# PUBLICATION_FORM_MAPPINGS is a list of dictionaries that contain the
# following parameters:
# dataset_schema: the namespace of the schema that triggers the form to be used
# publication_schema: the namspace of the schema that should be added to the
# publication
# form_template: a URL to the form template (usually static HTML)
PUBLICATION_FORM_MAPPINGS = [
    {'dataset_schema': 'http://example.com/a_dataset_schema',
     'publication_schema': 'http://example.com/a_publication_schema',
     'form_template': '/static/publication-form/form-template.html'}]
# Note: dataset_schema is treated as a regular expression

# The PDB publication schema is used for any experiments that reference a
# PDB structure
# It is defined here as a setting because it is used both for the publication
# form and for fetching data from PDB.org and must always match.
PDB_PUBLICATION_SCHEMA_ROOT = 'http://synchrotron.org.au/pub/mx/pdb/'
PDB_SEQUENCE_PUBLICATION_SCHEMA = PDB_PUBLICATION_SCHEMA_ROOT+'sequence/'
PDB_CITATION_PUBLICATION_SCHEMA = PDB_PUBLICATION_SCHEMA_ROOT+'citation/'

# Used by the Australian Synchrotron for MX datasets
MX_PUBLICATION_DATASET_SCHEMA = 'http://synchrotron.org.au/pub/mx/dataset/'

from datetime import timedelta
PDB_REFRESH_INTERVAL = timedelta(days=7)

PUBLICATION_FORM_MAPPINGS = [
    {'dataset_schema': r'^http://synchrotron.org.au/mx/',
     'publication_schema': PDB_PUBLICATION_SCHEMA_ROOT,
     'form_template': '/static/publication-form/mx-pdb-template.html'},
    {'dataset_schema': r'^http://synchrotron.org.au/mx/',
     'publication_schema': MX_PUBLICATION_DATASET_SCHEMA,
     'form_template':
     '/static/publication-form/mx-dataset-description-template.html'}]

# Put your API_ID for the Monash DOI minting service here. For other DOI
# minting, please contact the developers
MODC_DOI_ENABLED = False  # Change me to true if you use this service
MODC_DOI_API_ID = ''
MODC_DOI_API_PASSWORD = ''
MODC_DOI_MINT_DEFINITION = 'https://doiserver/modc/ws/MintDoiService.wsdl'
MODC_DOI_ACTIVATE_DEFINITION = 'https://doiserver/modc/ws/' \
    'ActivateDoiService.wsdl'
MODC_DOI_DEACTIVATE_DEFINITION = 'https://doiserver/modc/ws/' \
    'DeactivateDoiService.wsdl'
MODC_DOI_ENDPOINT = 'https://doiserver/modc/ws/'
MODC_DOI_MINT_URL_ROOT = 'http://mytardisserver/'

# Change this to the user name of the data administrator if it should be someone other than the
# publication creator
PUBLICATION_DATA_ADMIN = None
