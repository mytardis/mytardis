'''
default settings for publication app
override in main settings
'''

from datetime import timedelta

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
# PUBLICATION_FORM_MAPPINGS = [
#    {'dataset_schema': 'http://example.com/a_dataset_schema',
#     'publication_schema': 'http://example.com/a_publication_schema',
#     'form_template': '/static/publication-form/form-template.html'}]
# Note: dataset_schema is treated as a regular expression

# The PDB publication schema is used for any experiments that reference a
# PDB structure
# It is defined here as a setting because it is used both for the publication
# form and for fetching data from PDB.org and must always match.
PDB_PUBLICATION_SCHEMA_ROOT = 'http://synchrotron.org.au/pub/mx/pdb/'
PDB_SEQUENCE_PUBLICATION_SCHEMA = PDB_PUBLICATION_SCHEMA_ROOT + 'sequence/'
PDB_CITATION_PUBLICATION_SCHEMA = PDB_PUBLICATION_SCHEMA_ROOT + 'citation/'

# Used by the Australian Synchrotron for MX datasets
MX_PUBLICATION_DATASET_SCHEMA = 'http://synchrotron.org.au/pub/mx/dataset/'

# Used for generic dataset descriptions (all datasets that are not MX)
GENERIC_PUBLICATION_DATASET_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'generic/'

PDB_REFRESH_INTERVAL = timedelta(days=7)

PUBLICATIONS_REQUIRE_APPROVAL = True

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
MODC_DOI_MINT_URL_ROOT = 'http://mytardisserver/'

# Change this to the user name of the data administrator if it should be someone other than the
# publication creator
PUBLICATION_DATA_ADMIN = None

# A dictionary of length=2 tuples, where the first entry is the email
# subject line, and the second is the message text
PUBLICATION_EMAIL_MESSAGES = {
    'requires_authorisation': ('[TARDIS] Publication requires authorisation',
                               '''\
Hello!
A publication has been submitted by "{user_name}" and requires approval by a \
publication administrator.
You may view the publication here: {pub_url}

This publication will not be publicly accessible until all embargo conditions \
are met following approval.
To approve this publication, please access the publication approvals \
interface here: {approvals_url}
'''),
    'awaiting_approval': ('[TARDIS] Publication submitted',
                          '''\
Hello!
Your publication, "{pub_title}", has been submitted and is awaiting approval \
by an administrator.
You will receive a notification once his has occurred.
'''),
    'approved': ('[TARDIS] Publication approved',
                 '''\
Hello!
Your publication, "{pub_title}", has been approved for release and will appear \
online following any embargo conditions. You may view your publication here: \
{pub_url}
'''),
    'approved_with_doi': ('[TARDIS] Publication approved',
                          '''\
Hello!
Your publication, "{pub_title}", has been approved for release and will appear \
online following any embargo conditions. You may view your publication here: \
{pub_url}

A DOI has been assigned to this publication ({doi}) \
and will become active once your publication is released.
You may use cite using this DOI immediately.
'''),
    'rejected': ('[TARDIS] Publication rejected',
                 '''\
Hello!
Your publication, "{pub_title}", is unable to be released. Please contact your \
system administrator for further information.
'''),
    'reverted_to_draft': ('[TARDIS] Publication reverted to draft',
                          '''\
Hello!
Your publication, "{pub_title}", has been reverted to draft and may now be \
amended.
'''),
    'released': ('[TARDIS] Publication released',
                 '''\
Hello,
Your publication, "{pub_title}", is now public!
'''),
    'released_with_doi': ('[TARDIS] Publication released',
                          '''\
Hello,
Your publication, "{pub_title}", is now public!
You may view your publication here: http://dx.doi.org/{doi}
''')
}
