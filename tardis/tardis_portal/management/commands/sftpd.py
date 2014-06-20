import logging
from optparse import make_option

from django.core.management.base import BaseCommand

import tardis.tardis_portal.sftp as sftp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-H', '--host',
                    action='store',
                    type='string',
                    dest='host',
                    default=None,
                    help='Host name to bind'),
        )

    def handle(self, *args, **kwargs):
        sftp.start_server(host=kwargs['host'])
