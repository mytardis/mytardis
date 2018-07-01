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

# PUBLICATION_SCHEMA_ROOT = 'http://www.mytardis.org/schemas/publication/'

# This schema holds bibliographic details including authors and
# acknowledgements
# PUBLICATION_DETAILS_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'details/'

# Any experiment with this schema is treated as a draft publication
# This schema will be created automatically if not present
# PUBLICATION_DRAFT_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'draft/'

# Put your API_ID for the Monash DOI minting service here. For other DOI
# minting, please contact the developers
# MODC_DOI_ENABLED = False
# MODC_DOI_API_ID = ''
# MODC_DOI_API_PASSWORD = ''
# MODC_DOI_MINT_DEFINITION = 'https://doiserver/modc/ws/MintDoiService.wsdl'
# MODC_DOI_ACTIVATE_DEFINITION = 'https://doiserver/modc/ws/' \
#     'ActivateDoiService.wsdl'
# MODC_DOI_DEACTIVATE_DEFINITION = 'https://doiserver/modc/ws/' \
#     'DeactivateDoiService.wsdl'
# MODC_DOI_MINT_URL_ROOT = 'http://mytardisserver/'

# Push-to app settings
# PUSH_TO_FROM_EMAIL = 'noreply@example.com'
