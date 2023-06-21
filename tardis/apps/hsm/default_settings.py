HSM_DATASET_NAMESPACE = "http://mytardis.org/schemas/hsm/dataset/1"

HSM_MAX_INODE_FILE_SIZE = 384
'''
The maximum size of files that can be stored
within the inode (with stat reporting 0 blocks).

To determine the right value for your filesystem,
you can create some small test files and check
how small they have to be to have stat report 0 blocks.

https://en.wikipedia.org/wiki/Inode#Inlining
'''

HSM_EMAIL_TEMPLATES = {
    'dfo_recall_complete': ('[{site_title}] File recalled from archive',
                           '''\
Dear {first_name} {last_name},

The following file has has been recalled from the archive:

{file_path}

It can be downloaded from: {download_url}

Please contact {support_email} if you did not \
request this file or if you think you received this email by error.

Regards,
{site_title} Team.
'''),
    'dfo_recall_failed': ('[{site_title}] File recall failed',
                           '''\
Dear {first_name} {last_name},

An error occurred when attempting to recall the following file from the archive:

{file_path}

Please try again later, or contact {support_email} for assistance.

Regards,
{site_title} Team.
'''),
    'dataset_recall_requested': ('[{site_title}] Dataset recall requested',
                           '''\
Dear RDSM support team,

User {user} has requested to recall dataset {dataset} from HSM vault.

The path to the dataset is {path}


Regards,
{site_title} Team.
''')
}
