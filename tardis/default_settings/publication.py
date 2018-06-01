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
