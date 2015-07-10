import logging
from itertools import chain
from os import path
from StringIO import StringIO
from urllib2 import urlopen

from tardis.tardis_portal.models import Schema, DatafileParameterSet,\
    ParameterName, DatasetParameter
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
from tardis.tardis_portal.models.parameters import DatasetParameter

logger = logging.getLogger(__name__)

class JEOLSEMFilter(object):
    """This filter collects metadata from JEOL SEM text files.

    :param name: the short name of the schema.
    :type name: string
    :param schema: the name of the schema to load the EXIF data into.
    :type schema: string
    """

    ATTR_PREFIXES = ('$CM_', '$$SM_')

    SCHEMA = 'http://www.jeol.com/#jeol-sem-schema'

    def __init__(self):
        pass


    def __call__(self, sender, **kwargs):
        """post save callback entry point.

        :param sender: The model class.
        :param instance: The actual instance being saved.
        :param created: A boolean; True if a new record was created.
        :type created: bool
        """
        datafile = kwargs.get('instance')

        try:
            logger.debug('Checking if file is JEOL metadata')
            if self.is_text_file(datafile):
                # Don't check further if it's already processed
                if self.is_already_processed(datafile):
                    logger.debug('JEOL metadata file was already processed.')
                    return
                # Get file contents (remotely if required)
                contents = self.get_file_contents(datafile)
                if self.is_jeol_sem_metadata(contents):
                    schema = self._get_schema()
                    logger.debug('Parsing JEOL metadata file')
                    self.save_metadata(datafile, schema,
                                       self.get_metadata(schema, contents))
        except Exception, e:
            logger.debug(e)
            return

    def _get_schema(self):
        """Return the schema object that the paramaterset will use.
        """
        try:
            return Schema.objects.get(namespace__exact=self.SCHEMA)
        except Schema.DoesNotExist:
            from django.core.management import call_command
            call_command('loaddata', 'jeol_metadata_schema')
            return self._get_schema()

    def is_already_processed(self, datafile):
        def get_filename(ps):
            try:
                return ParameterSetManager(ps)\
                        .get_param('metadata-filename', True)
            except DatasetParameter.DoesNotExist:
                return None

        def processed_files(dataset):
            return [get_filename(ps)
                    for ps in datafile.dataset.getParameterSets()]

        return datafile.filename in processed_files(datafile.dataset)

    def is_text_file(self, datafile):
        return datafile.get_mimetype().startswith('text/plain')

    def get_file_contents(self, datafile):
        from contextlib import closing
        file_ = datafile.get_file()
        if file_ is None:
            return ''
        with closing(file_) as f:
            return f.read()

    def is_jeol_sem_metadata(self, filedata):
        for line in StringIO(filedata):
            if line.startswith('$CM_FORMAT '):
                return True
        return False


    def get_metadata(self, schema, filedata):
        known_attributes = [pn.name
                            for pn
                            in ParameterName.objects.filter(schema=schema)]

        def get_key_value(line, prefix):
            if not line.startswith(prefix):
                return None
            try:
                key, value = line[len(prefix):].strip().split(' ')
                if not key.lower() in known_attributes:
                    return None
            except ValueError:
                # Not a key value pair
                return None
            return (key.lower(), value)

        def process_line(line):
            return filter(None, [get_key_value(line, prefix)
                                 for prefix in self.ATTR_PREFIXES])

        return chain.from_iterable(map(process_line, StringIO(filedata)))


    def save_metadata(self, datafile, schema, metadata):
        psm = ParameterSetManager(parentObject=datafile.dataset,
                                  schema=schema.namespace)
        psm.set_param('metadata-filename', datafile.filename)
        for key, value in metadata:
            try:
                psm.set_param(key, value)
            except ValueError, e:
                pn = ParameterName.objects.get(name=key, schema=schema)
                psm.set_param(key, value.strip(pn.units))
