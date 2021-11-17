"""
Management command to cascade Macro(experiment)-level ACLs down to Micro(all)-levels.
Once executed, Macro and Micro level permissions should essentially be "in sync"
allowing for an easier transition across from Macro to Micro level ACLs for existing
databases.

The script inspects all ExperimentACLs for a given Experiment, and creates a
corresponding (Dataset+Datafile)ACL for each Dataset and DataFile in the Experiment.
i.e.
If an experiment has two ExperimentACLs, two ACLs will be created for each Dataset
and DataFile below the Experiment. The DatasetACLs/DatafileACLs will mimic the
ExperimentACLs they stem from: they will have the same Boolean permission flags and
link to the same Users/Groups/Tokens that the correpsonding ExperimentACL linked to.

"""

import sys

from django.core.management.base import BaseCommand

from ...models.access_control import  DatasetACL, DatafileACL
from ...models import Experiment

class Command(BaseCommand):

    help = 'Create Dataset+Datafile ACLs from ACLs of parent Experiment'

    def handle(self, *args, **options):

        sys.stderr.write("Iterating over Experiments.\n")

        for exp in Experiment.objects.all().only("id").iterator():
            sys.stderr.write("Processing Experiment_ID="+str(exp.id)+" ...\n")
            acls_to_cascade = exp.experimentacls.select_related("user", "group", "token"
                                        ).all().values("user__id", "group__id", "token__id",
                                    "canRead", "canDownload", "canWrite", "canSensitive",
                                    "canDelete", "isOwner", "aclOwnershipType", "effectiveDate",
                                    "expiryDate")

            dataset_ids = exp.datasets.all().values_list("id", flat=True)
            for ds in dataset_ids:
                sys.stderr.write("Creating ACLs for Dataset_ID="+str(ds)+".\n")
                new_acls = [DatasetACL(dict(item, **{'dataset_id':ds})) for item in acls_to_cascade]
                DatasetACL.objects.bulk_create(new_acls)
                sys.stderr.write("Datasets done.\n")

            datafile_ids = exp.datasets.prefetch_related("datafile").all().values_list("datafile__id", flat=True)
            for df in datafile_ids:
                sys.stderr.write("Creating ACLs for DataFile_ID="+str(df)+".\n")
                new_acls = [DatafileACL(dict(item, **{'dataset_id':df})) for item in acls_to_cascade]
                DatafileACL.objects.bulk_create(new_acls)
                sys.stderr.write("DataFiles done.\n")
        sys.stderr.write("All done.\n")
