"""
Management utility to create a token user
"""

import hashlib
from contextlib import closing
from urllib2 import urlopen

from django.core.management.base import BaseCommand, CommandError
from tardis.tardis_portal.models import DataFile

CHUNK_SIZE = 32*1024

class AlgorithmNotSupported(Exception):
    pass

class NoHashAvailable(Exception):
    pass

class ValidationFailed(Exception):
    pass

class Command(BaseCommand):

    help = 'Used to check file hashes against actual files.'

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', 1))

        for df in DataFile.objects.all():
            for algorithm in ('sha512', 'md5'):
                try:
                    validate_digest(algorithm, df)
                    # Success, so don't try another
                    break
                except AlgorithmNotSupported:
                    continue
                except NoHashAvailable:
                    continue
                except ValidationFailed:
                    self.stdout.write("%d/%s: FAILED\n" % (df.dataset.id, df))
                if verbosity > 1:
                    self.stdout.write("%d/%s: OK\n" % (df.dataset.id, df))



def validate_digest(algorithm, datafile):
    try:
        expected = getattr(datafile, "%ssum" % algorithm)
    except AttributeError:
        raise AlgorithmNotSupported()

    if not expected:
        raise NoHashAvailable()

    url = datafile.get_actual_url()
    if not url:
        raise ValidationFailed()

    digest = getattr(hashlib, algorithm)()
    with closing(urlopen(url)) as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), ''):
            digest.update(chunk)

    if expected != digest.hexdigest():
        raise ValidationFailed
