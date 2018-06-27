import logging
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

import tardis.tardis_portal.sftp as sftp

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments:

        # Named (optional) arguments:
        parser.add_argument(
            '-H', '--host',
            dest='host',
            default=None,
            help='Host name to bind to'
        )
        parser.add_argument(
            '-P', '--port',
            dest='port',
            default=getattr(settings, 'SFTP_PORT', 2200),
            type=int,
            help='Port to listen on, default: 2200'
        )

    def handle(self, *args, **options):
        host = options.get('host', None)
        port = options.get('port', 2200)
        sftp.start_server(host=host, port=port)
