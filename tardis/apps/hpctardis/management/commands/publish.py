from django.core.management.base import BaseCommand, CommandError
from tardis.tardis_portal.models import Experiment

from tardis.apps.hpctardis.views import _promote_experiments_to_public
from tardis.apps.hpctardis.models import PublishAuthorisation

from tardis.apps.hpctardis.publish.RMITANDSService import send_request_email


class Command(BaseCommand):
    
    help = "help me"
    
    def handle(self, *args, **options):
            
        if len(args) < 1:
            self.stdout.write("no command specified\n")
            return
        
        if args[0] == 'resend':
            # Resend all outstanding auth emails for experiments
            
            expid = args[1]
            
            try:
                exp = Experiment.objects.get(id=expid,public=False)
            except Experiment.DoesNotExist:
                self.stderr.write("pending experiment does not exist")
                return
            
            
            publish_auths= PublishAuthorisation.objects.filter(experiment=exp)
            
            for publish_auth in publish_auths:
                if publish_auth.status == PublishAuthorisation.PENDING_APPROVAL:
                    send_request_email(publish_auth.party_record,
                                    publish_auth.activity_record,expid)
                
            
                        
            self.stdout.write('done\n')
            
        elif args[0] == 'promote':
            # Check PublishAuthEvents and make experiment public if fully
            # approved
            expid = args[1]
            
            try:
                exp = Experiment.objects.get(id=expid)
            except Experiment.DoesNotExist:
                self.stderr.write("experiment does not exist")
                return
            
            message = _promote_experiments_to_public(exp)
            self.stdout.write('done')
            self.stdout.write("process reports: %s" % message)
            self.stdout.write("done")
            
        elif args[0] == "test":
            self.stdout.write('done\n')
        else:
            self.stdout.write("no command specified\n")
