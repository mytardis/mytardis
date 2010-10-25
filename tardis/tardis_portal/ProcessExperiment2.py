'''
The new ProcessExperiment module.

@author: Gerson Galang
'''

from tardis.tardis_portal.ProcessExperiment import ProcessExperiment
from tardis.tardis_portal.logger import logger
from tardis.tardis_portal.metsparser import MetsExperimentStructCreator
from tardis.tardis_portal.metsparser import MetsMetadataInfoHandler
from tardis.tardis_portal.metsparser import MetsDataHolder
from xml.sax.handler import feature_namespaces
from xml.sax import make_parser

from django.db import transaction


class ProcessExperiment2(ProcessExperiment):

    def register_experiment_xmldata_file(self, filename, created_by,
            expid=None):
        '''
        Override the ProcessExperiment's register_experiment_xmldata_file()
        function.

        Arguments:
        filename -- path of the document to parse (METS or notMETS)
        created_by -- a User instance
        expid -- the experiment ID to use

        Returns:
        The experiment ID

        '''

        f = open(filename)

        firstline = f.readline()

        f.close()

        if firstline.startswith('<experiment'):
            logger.debug('processing simple xml')
            eid = self.process_simple(filename, created_by, expid)
        else:
            logger.debug('processing METS')
            eid = self.parseMets(filename, created_by, expid)

        return eid

    @transaction.commit_on_success()
    def parseMets(self, filename, createdBy, expId=None):
        '''Parse the METS document using the SAX Parser classes provided in the
        metsparser module.

        Arguments:
        filename -- path of the document to parse (METS or notMETS)
        created_by -- a User instance
        expid -- the experiment ID to use

        Returns:
        The experiment ID

        '''

        import time
        startParseTime = time.time()

        logger.debug('parse experiment id: ' + str(expId))

        parser = make_parser(["drv_libxml2"])
        parser.setFeature(feature_namespaces, 1)
        dataHolder = MetsDataHolder()

        # on the first pass, we'll parse the document just so we can
        # create the experiment's structure
        parser.setContentHandler(MetsExperimentStructCreator(dataHolder))
        parser.parse(filename)

        # on the second pass, we'll parse the document so that we can tie
        # the metadata info with the experiment/dataset/datafile objects
        parser.setContentHandler(
            MetsMetadataInfoHandler(dataHolder, expId, createdBy))
        parser.parse(filename)

        endParseTime = time.time()

        # time difference in seconds
        timeDiff = endParseTime - startParseTime
        logger.debug('time difference in seconds: %s' % (timeDiff))

        return dataHolder.experimentDatabaseId
