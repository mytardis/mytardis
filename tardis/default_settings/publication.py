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
