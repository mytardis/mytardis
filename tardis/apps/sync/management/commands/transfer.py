
from django.core.management.base import BaseCommand, CommandError
from tardis.apps.sync.transfer_service import TransferService
from django.contrib.auth.models import User

from tardis.tardis_portal.models.experiment import Experiment, ExperimentACL

class Command(BaseCommand):
    # TODO slightly more flexible command line options
    args = '<epn>'
    help = 'Transfer an experiment to home institution(s)'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Please provide an EPN')
        
        epn = args[0]


        try:
            experiment = Experiment.objects.get(
                    experimentparameterset__experimentparameter__name__name='EPN',
                    experimentparameterset__experimentparameter__string_value=epn)
        except Experiment.DoesNotExist:
            raise CommandError('Invalid EPN (%s) provided' % (epn))
        
        try:
            owner_emails = []
            owner_emails.extend([user.email for user in experiment.get_owners()])
                
        except User.DoesNotExist:
            raise CommandError("No users found for experiment EPN:%s" % (epn))
        
        try:
            ts = TransferService()
            sites = ts.push_experiment_to_institutions(experiment, owner_emails)
            for url, status in sites:
                self.stdout.write('Pushed to url %s %s' % (url, 'succesfully' if status else 'unsuccessfully'))
		
        except TransferService.TransferError, e:
            raise CommandError('Error transferring experiment(EPN:%s): %s' % (epn, e))
