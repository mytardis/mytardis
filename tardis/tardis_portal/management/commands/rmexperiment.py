"""
Management command to delete the specified experiment and its associated
datasets, datafiles and parameters.

The operation is atomic, either the entire experiment is deleted, or nothing.

rmexperiment was introduced due to the Oracle DISTINCT workaround causing
sql delete cascading to fail.  The current implementation of rmexperiment still relies on
some cascading.
"""

import sys
import traceback
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, DEFAULT_DB_ALIAS
from tardis.tardis_portal.models import Experiment, Dataset, DataFile
from tardis.tardis_portal.models import ExperimentAuthor, ObjectACL
from tardis.tardis_portal.models import ExperimentParameterSet, ExperimentParameter
from tardis.tardis_portal.models import DatasetParameterSet
from tardis.tardis_portal.models import DatafileParameterSet

class Command(BaseCommand):
    args = '<MyTardis Exp ID>'
    help = 'Delete the supplied MyTardis Experiment ID'
    option_list = BaseCommand.option_list + (
        make_option('--list',
                    action='store_true',
                    dest='list',
                    default=False,
                    help="Only list the experiment to be deleted, don't actually delete"),
        ) + (
        make_option('--confirmed',
                    action='store_true',
                    dest='confirmed',
                    default=False,
                    help="Don't ask the user, just do the deletion"),
        )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Expected exactly 1 argument - Experiment ID")
        try:
            exp = Experiment.objects.get(pk=int(args[0]))
        except Experiment.DoesNotExist:
            raise CommandError("Experiment ID %s not found" % args[0])

        # FIXME - we are fetch a bunch of stuff outside of any transaction, and then
        # doing the deletes in a transaction.  There is an obvious race condition here
        # that may result in components of an experiment not being deleted or being deleted
        # when they shouldn't be.

        # Fetch Datasets and Datafiles and work out which ones would be deleted
        datasets = Dataset.objects.filter(experiments__id=exp.id)
        datafiles = DataFile.objects.filter(dataset__id__in=map((lambda ds : ds.id), datasets))
        uniqueDatasets = filter((lambda ds : ds.experiments.count() == 1), datasets)
        uniqueDatasetIds = map((lambda ds : ds.id), uniqueDatasets)
        uniqueDatafiles = filter((lambda df : df.dataset.id in uniqueDatasetIds), datafiles)

        # Fetch other stuff to be printed and deleted.
        acls = ObjectACL.objects.filter(content_type=exp.get_ct(),
                                        object_id=exp.id)
        authors = ExperimentAuthor.objects.filter(experiment=exp)
        epsets = ExperimentParameterSet.objects.filter(experiment=exp)

        confirmed = options.get('confirmed', False)
        listOnly = options.get('list', False)
        if not listOnly and not confirmed:
            self.stdout.write("Delete the following experiment?\n\n")

        if listOnly or not confirmed:
            # Print basic experiment information
            self.stdout.write("Experiment\n    ID: {0}\n".format(exp.id))
            self.stdout.write("    Title: {0}\n".format(exp.title))
            self.stdout.write("    Locked: {0}\n".format(exp.locked))
            self.stdout.write("    Public Access: {0}\n".format(exp.public_access))

            # List experiment authors
            self.stdout.write("    Authors:\n")
            for author in authors:
                self.stdout.write("        {0}\n".format(author.author))

            # List experiment metadata
            for epset in epsets:
                self.stdout.write("    Param Set: {0} - {1}\n".format(epset.schema.name, epset.schema.namespace))
                params = ExperimentParameter.objects.filter(parameterset=epset)
                for param in params:
                    self.stdout.write("        {0} = {1}\n".format(param.name.full_name, param.get()))

            # List experiment ACLs
            self.stdout.write("    ACLs:\n")
            for acl in acls:
                self.stdout.write("        {0}-{1}, flags: ".format(acl.pluginId, acl.entityId))
                if acl.canRead:
                    self.stdout.write("R")
                if acl.canWrite:
                    self.stdout.write("W")
                if acl.canDelete:
                    self.stdout.write("D")
                if acl.isOwner:
                    self.stdout.write("O")
                self.stdout.write("\n")

            # Basic Statistics
            self.stdout.write("    {0} total dataset(s), containing {1} file(s)\n".format(
                    datasets.count(), datafiles.count()))
            self.stdout.write("    {0} non-shared dataset(s), containing {1} file(s)\n".format(
                    len(uniqueDatasets), len(uniqueDatafiles)))
            if len(uniqueDatasets) > 0 and not listOnly :
                self.stdout.write("        (The non-shared datasets and files will be deleted)\n")

        # If the user has only requested a listing finish now
        if listOnly:
            return

        if not confirmed:
            # User must enter "yes" to proceed
            self.stdout.write("\n\nConfirm Deletion? (yes): ")
            ans = sys.stdin.readline().strip()
            if ans != "yes":
                self.stdout.write("'yes' not entered, aborting.\n")
                return

        # Consider the entire experiment deletion atomic
        using = options.get('database', DEFAULT_DB_ALIAS)
        transaction.set_autocommit(False, using=using)

        try:
            acls.delete()
            epsets.delete()
            for dataset in datasets:
                dataset.experiments.remove(exp.id)
                if dataset.experiments.count() == 0:
                    DatasetParameterSet.objects.filter(dataset=dataset).delete()
                    for datafile in DataFile.objects.filter(dataset=dataset):
                        DatafileParameterSet.objects.filter(datafile=datafile).delete()
                        datafile.delete()
                    dataset.delete()
            authors.delete()
            exp.delete()

            transaction.commit(using=using)
        except Exception:
            transaction.rollback(using=using)
            exc_class, exc, tb = sys.exc_info()
            new_exc = CommandError(
                "Exception %s has occurred: rolled back transaction"
                % (exc or exc_class))
            raise new_exc.__class__, new_exc, tb
        finally:
            transaction.set_autocommit(True, using=using)
