'''
default settings for publication app
override in main settings
'''

from datetime import timedelta

PUBLICATION_INTRODUCTION = """
<h2>MyTardis Publishing Form</h2>

<p>This form will help MyTardis to describe and provide online access to your data.</p>

<p>
Once data has been released for publication, you will receive
a <a target="_blank"
href="http://en.wikipedia.org/wiki/Digital_object_identifier">DOI</a>
link to this data for citation.
</p>

<p>Follow the form to identify datasets and provide additional information.</p>

<p>
Data will be released under
a <a target="_blank"
href="http://creativecommons.org/licenses/by/3.0/au/deed.en">Creative
Commons BY</a> license: Whenever a work is copied or redistributed
under a Creative Commons BY licence, the original creator (and any
other nominated parties) must be credited and the source linked to.
</p>
<p>
For further enquiries, please contact:
<a target="_blank" href="mailto:store.star.help@monash.edu">store.star.help@monash.edu</a>.
</p>
"""

PUBLICATION_NOTIFICATION_SENDER_EMAIL = 'emailsender@mytardisserver'
PUBLICATION_OWNER_GROUP = 'publication-admin'
PUBLICATION_SCHEMA_ROOT = 'http://www.tardis.edu.au/schemas/publication/'

# This schema holds bibliographic details including authors and
# acknowledgements
PUBLICATION_DETAILS_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'details/'

# Any experiment with this schema is treated as a draft publication
# This schema will be created automatically if not present
PUBLICATION_DRAFT_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'draft/'

# Used for recording extra information about datasets
GENERIC_PUBLICATION_DATASET_SCHEMA = PUBLICATION_SCHEMA_ROOT + 'generic/'

# PUBLICATIONS_REQUIRE_APPROVAL was set to True for Store.Synchrotron, but in
# the general case, there is no governing body overseeing data publication -
# it is just up to the researchers who have uploaded the data.
PUBLICATIONS_REQUIRE_APPROVAL = False

# If set to True, attempting to submit a draft for publication will fail if an
# email notification can't be sent.  Allowing submission of publications without
# email notifications is useful for local testing.
PUBLICATIONS_REQUIRE_EMAIL_SUCCESS = False

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
