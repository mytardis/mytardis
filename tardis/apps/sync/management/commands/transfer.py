from django.core.management.base import BaseCommand, CommandError
from tardis.apps.sync.transfer_serivce import TransferService, \
        SyncManagerTransferError, SyncManagerInvalidUIDError

class Command(BaseCommand):
    args = '<uid>'
    help = 'Transfer an experiment to home institution(s)'

    def handle(self, *args, **options):
        ts = TransferService()
        if len(args) != 1:
            raise CommandError('Please provide a uid')
        
        uid = args[0]
        site_settings_url = '' 

        try:
            ts.start_file_transfer(uid, site_settings_url)
        except SyncManagerInvalidUIDError:
            raise CommandError('Invalid UID (%s) provided' % (uid))
        except SyncManagerTransferError, e:
            raise CommandError('Error transferring experiment: %s' % (e))


