from os import path

REQUIRE_VALID_PUBLIC_CONTACTS = True

# RIF-CS Settings
OAI_DOCS_PATH = path.abspath(path.join(path.dirname(__file__), '../../var/oai'))
RIFCS_PROVIDERS = (
    'tardis.tardis_portal.publish.provider.rifcsprovider.RifCsProvider',)
RIFCS_TEMPLATE_DIR = path.join(
    path.dirname(__file__), '..',
    'tardis_portal/templates/tardis_portal/rif-cs/profiles/')
RIFCS_GROUP = "MyTARDIS Default Group"
RIFCS_KEY = "keydomain.example"
RELATED_INFO_SCHEMA_NAMESPACE = \
    'http://www.tardis.edu.au/schemas/related_info/2011/11/10'
RELATED_OTHER_INFO_SCHEMA_NAMESPACE = \
    'http://www.tardis.edu.au/schemas/experiment/annotation/2011/07/07'

DOI_ENABLE = False
DOI_XML_PROVIDER = 'tardis.tardis_portal.ands_doi.DOIXMLProvider'
# DOI_TEMPLATE_DIR = path.join(
#    TARDIS_DIR, 'tardis_portal/templates/tardis_portal/doi/')
DOI_TEMPLATE_DIR = path.join('tardis_portal/doi/')
DOI_APP_ID = ''
DOI_NAMESPACE = 'http://www.tardis.edu.au/schemas/doi/2011/12/07'
DOI_MINT_URL = 'https://services.ands.org.au/home/dois/doi_mint.php'
DOI_RELATED_INFO_ENABLE = False
DOI_BASE_URL = 'http://mytardis.example.com'

OAIPMH_PROVIDERS = [
    'tardis.apps.oaipmh.provider.experiment.DcExperimentProvider',
    'tardis.apps.oaipmh.provider.experiment.RifCsExperimentProvider',
]

# Example settings for the publication form workflow. Also requires the
# corresponding app in 'INSTALLED_APPS' and the corresponding task to be
# enabled

# Publication form settings #
# PUBLICATION_NOTIFICATION_SENDER_EMAIL = 'emailsender@mytardisserver'

# PUBLICATION_OWNER_GROUP = 'publication-admin'

# PUBLICATION_SCHEMA_ROOT = 'http://www.tardis.edu.au/schemas/publication/'

# This schema holds bibliographic details including authors and
# acknowledgements
# PUBLICATION_DETAILS_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'details/'

# Any experiment with this schema is treated as a draft publication
# This schema will be created automatically if not present
# PUBLICATION_DRAFT_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'draft/'

# Form mappings
# PUBLICATION_FORM_MAPPINGS is a list of dictionaries that contain the
# following parameters:
# dataset_schema: the namespace of the schema that triggers the form to be used
# publication_schema: the namspace of the schema that should be added to the
# publication
# form_template: a URL to the form template (usually static HTML)
# PUBLICATION_FORM_MAPPINGS = [
#     {'dataset_schema': 'http://example.com/a_dataset_schema',
#      'publication_schema': 'http://example.com/a_publication_schema',
#      'form_template': '/static/publication-form/form-template.html'}]
# Note: dataset_schema is treated as a regular expression

# The PDB publication schema is used for any experiments that reference a
# PDB structure
# It is defined here as a setting because it is used both for the publication
# form and for fetching data from PDB.org and must always match.
# PDB_PUBLICATION_SCHEMA_ROOT = 'http://synchrotron.org.au/pub/mx/pdb/'
# PDB_SEQUENCE_PUBLICATION_SCHEMA = PDB_PUBLICATION_SCHEMA_ROOT+'sequence/'
# PDB_CITATION_PUBLICATION_SCHEMA = PDB_PUBLICATION_SCHEMA_ROOT+'citation/'
# PDB_REFRESH_INTERVAL = timedelta(days=7)

# PUBLICATION_FORM_MAPPINGS = [
#     {'dataset_schema': r'^http://synchrotron.org.au/mx/',
#      'publication_schema': PDB_PUBLICATION_SCHEMA_ROOT,
#      'form_template': '/static/publication-form/mx-pdb-template.html'},
#     {'dataset_schema': r'^http://synchrotron.org.au/mx/',
#      'publication_schema': 'http://synchrotron.org.au/pub/mx/dataset/',
#      'form_template':
#      '/static/publication-form/mx-dataset-description-template.html'}]

# Put your API_ID for the Monash DOI minting service here. For other DOI
# minting, please contact the developers
# MODC_DOI_API_ID = ''
# MODC_DOI_API_PASSWORD = ''
# MODC_DOI_MINT_DEFINITION = 'https://doiserver/modc/ws/MintDoiService.wsdl'
# MODC_DOI_ACTIVATE_DEFINITION = 'https://doiserver/modc/ws/' \
#     'ActivateDoiService.wsdl'
# MODC_DOI_DEACTIVATE_DEFINITION = 'https://doiserver/modc/ws/' \
#     'DeactivateDoiService.wsdl'
# MODC_DOI_ENDPOINT = 'https://doiserver/modc/ws/'
# MODC_DOI_MINT_URL_ROOT = 'http://mytardisserver/'

# Push-to app settings
# PUSH_TO_FROM_EMAIL = 'noreply@example.com'
