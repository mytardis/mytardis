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

        for exp in Experiment.objects.all().only("id", "public_access").iterator():
            sys.stderr.write("Processing Experiment_ID="+str(exp.id)+" ...\n")
            acls_to_cascade = exp.experimentacl_set.select_related("user", "group", "token"
                                        ).all().values("user__id", "group__id", "token__id",
                                    "canRead", "canDownload", "canWrite", "canSensitive",
                                    "canDelete", "isOwner", "aclOwnershipType", "effectiveDate",
                                    "expiryDate")

            public_to_cascade = int(exp.public_access)

            datasets = exp.datasets.all()
            for ds in datasets:
                sys.stderr.write("Creating ACLs for Dataset_ID="+str(ds.id)+".\n")
                new_acls = [DatasetACL(dict(item, **{'dataset_id':ds.id})) for item in acls_to_cascade]
                DatasetACL.objects.bulk_create(new_acls)
                if ds.public_access < public_to_cascade:
                    sys.stderr.write("Cascading public_access flag to Dataset.\n")
                    ds.public_access = public_to_cascade
                    ds.save()

                datafiles = ds.datafile_set.all()
                for df in datafiles:
                    sys.stderr.write("Creating ACLs for DataFile_ID="+str(df.id)+".\n")
                    new_acls = [DatafileACL(dict(item, **{'dataset_id':df.id})) for item in acls_to_cascade]
                    DatafileACL.objects.bulk_create(new_acls)
                    if df.public_access < public_to_cascade:
                        sys.stderr.write("Cascading public_access flag to DataFile.\n")
                        df.public_access = public_to_cascade
                        df.save()
                sys.stderr.write("DataFiles done.\n")
            sys.stderr.write("Datasets done.\n")

        sys.stderr.write("All done.\n")
