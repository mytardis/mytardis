import logging
from optparse import make_option

from django.conf import settings
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
                    help='Host name to bind to'),
        make_option('-P', '--port',
                    action='store',
                    type='int',
                    dest='port',
                    default=getattr(settings, 'SFTP_PORT', 2200),
                    help='Port to listen on, default: 2200'),
    )

    def handle(self, *args, **kwargs):
        sftp.start_server(host=kwargs['host'], port=kwargs['port'])
