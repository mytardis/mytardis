"""
Management command to delete the specified experiment and its associated 
datasets, datafiles and parameters.

The operation is atomic, either the entire experiment is deleted, or nothing.

rmexperiment was introduced due to the Oracle DISTINCT workaround causing
sql delete cascading to fail.  The current implementation of rmexperiment still relies on
some cascading.
""" 

import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, DEFAULT_DB_ALIAS
from tardis.tardis_portal.models import Experiment, Dataset, Dataset_File
from tardis.tardis_portal.models import Author_Experiment, ExperimentACL
from tardis.tardis_portal.models import ExperimentParameterSet, ExperimentParameter
from tardis.tardis_portal.models import DatasetParameterSet
from tardis.tardis_portal.models import DatafileParameterSet

class Command(BaseCommand):
    args = '<MyTARDIS Exp ID>'
    help = 'Delete the supplied MyTARDIS Experiment ID'
    option_list = BaseCommand.option_list + (
        make_option('--list',
                    action='store_true',
                    dest='list',
                    default=False,
                    help="Only list the experiment to be deleted, don't actually delete"),
        )
    
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Expected exactly 1 argument - Experiment ID")
        try:
            exp = Experiment.objects.get(pk=int(args[0]))
        except Experiment.DoesNotExist:
            raise CommandError("Experiment ID %s not found" % args[0])

        self.stdout.write("Delete the following experiment?\n\n")

        # Print basic experiment information
        self.stdout.write("Experiment\n    ID: {0}\n".format(exp.id))
        self.stdout.write("    Title: {0}\n".format(exp.title))
        self.stdout.write("    Public: {0}\n".format(exp.public))
        
        # List experiment authors
        authors = Author_Experiment.objects.filter(experiment=exp)
        self.stdout.write("    Authors:\n")
        for author in authors:
            self.stdout.write("        {0}\n".format(author.author))
        
        # List experiment metadata
        epsets = ExperimentParameterSet.objects.filter(experiment=exp)
        for epset in epsets:
            self.stdout.write("    Param Set: {0} - {1}\n".format(
                epset.schema.name, epset.schema.namespace))
            params = ExperimentParameter.objects.filter(parameterset=epset)
            for param in params:
                self.stdout.write("        {0} = {1}\n".format(param.name.full_name, param.get()))
        
        # List experiment ACLs
        acls = ExperimentACL.objects.filter(experiment=exp)
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
        datasets = Dataset.objects.filter(experiment=exp)
        datafiles = Dataset_File.objects.filter(dataset__experiment=exp)
        self.stdout.write("    {0} datset(s), containing {1} file(s)\n".format(
                    datasets.count(), datafiles.count()))
        
        
        # If the user has only requested a listing finish now 
        if options.get('list', False):
            return
        
        # User must enter "yes" to proceed
        self.stdout.write("\n\nConfirm Deletion? (yes): ")
        ans = sys.stdin.readline().strip()
        if ans != "yes":
            self.stdout.write("'yes' not entered, aborting.\n")
            return
        
        # Consider the entire experiment deletion atomic
        using = options.get('database', DEFAULT_DB_ALIAS)
        transaction.commit_unless_managed(using=using)
        transaction.enter_transaction_management(using=using)
        transaction.managed(True, using=using)
        
        try:
            acls.delete()
            epsets.delete()
            DatasetParameterSet.objects.filter(dataset__experiment=exp).delete()
            DatafileParameterSet.objects.filter(dataset_file__dataset__experiment=exp).delete()
            authors.delete()
            datasets.delete()
            datafiles.delete()
            exp.delete()
        
            transaction.commit(using=using)
            transaction.leave_transaction_management(using=using)
        except:
            transaction.rollback(using=using)
            raise CommandError("Exception occurred, rolling back transaction")
