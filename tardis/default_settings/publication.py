from os import path

REQUIRE_VALID_PUBLIC_CONTACTS = True

# RIF-CS Settings
OAI_DOCS_PATH = path.abspath(path.join(path.dirname(__file__), "../../var/oai"))
RIFCS_PROVIDERS = ("tardis.tardis_portal.publish.provider.rifcsprovider.RifCsProvider",)
RIFCS_TEMPLATE_DIR = path.join(
    path.dirname(__file__),
    "..",
    "tardis_portal/templates/tardis_portal/rif-cs/profiles/",
)
RIFCS_GROUP = "MyTARDIS Default Group"
RIFCS_KEY = "keydomain.example"
RELATED_INFO_SCHEMA_NAMESPACE = (
    "http://www.tardis.edu.au/schemas/related_info/2011/11/10"
)
RELATED_OTHER_INFO_SCHEMA_NAMESPACE = (
    "http://www.tardis.edu.au/schemas/experiment/annotation/2011/07/07"
)

OAIPMH_PROVIDERS = [
    "tardis.apps.oaipmh.provider.experiment.DcExperimentProvider",
    "tardis.apps.oaipmh.provider.experiment.RifCsExperimentProvider",
]
