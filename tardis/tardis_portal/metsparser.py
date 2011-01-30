'''
The METS document parser.

Experiment/Dataset/Datafile metadata of this format can be easily parsed
by this module...

<trd:saxdatafile xmlns:trd="http://www.tardis.edu.au/schemas/saxs/datafile/2010/08/10">
    <trd:countingSecs>10.0</trd:countingSecs>
    <trd:io>274389</trd:io>
    <trd:ioBgnd>0</trd:ioBgnd>
    <trd:it>284</trd:it>
    <trd:itBgnd>0</trd:itBgnd>
    <trd:ibs>665765</trd:ibs>
    <trd:ibsBgnd>0</trd:ibsBgnd>
    <trd:timeStampString>Fri Apr 16 03:53:30 2010</trd:timeStampString>
    <trd:positionerString>UDEF1_2_PV1_2_3_4_5</trd:positionerString>
    <trd:positionerValues>24.7410 24.9764 20.000 12.000 26.322 2.0007 1.2999</trd:positionerValues>
</trd:saxdatafile>

As you can see, the structure is quite flat. The structure above is the
recommended way of defining metadata fields for Experiment/Dataset/Datafile.

If however the metadata structure will require going down into a number of
descendants below the child elements of the main metadata element, you'll need
to provide a custom METS handler for it. The MX schema is a good example of a
schema that does not conform to the key-value pair format this parser module
recommends.

<trd:mxdatafile xmlns:trd="http://www.tardis.edu.au/schemas/trdDatafile/1">
    <trd:imageType>R-AXIS</trd:imageType>
    <trd:oscillationRange>
        <trd:start>35.0</trd:start>
        <trd:end>35.5</trd:end>
    </trd:oscillationRange>
    <trd:exposureTime>3.5166667</trd:exposureTime>
    <trd:detectorSN>N/A</trd:detectorSN>
    <trd:xrayWavelength>1.5418</trd:xrayWavelength>
    <trd:directBeamXPos>149.59</trd:directBeamXPos>
    <trd:directBeamYPos>150.5</trd:directBeamYPos>
    <trd:detectorDistance>220.0</trd:detectorDistance>
    <trd:imageSizeX>3000.0</trd:imageSizeX>
    <trd:imageSizeY>3000.0</trd:imageSizeY>
    <trd:pixelSizeX>0.1</trd:pixelSizeX>
    <trd:pixelSizeY>0.1</trd:pixelSizeY>
    <trd:twoTheta>0.0</trd:twoTheta>
</trd:mxdatafile>

.. moduleauthor::  Gerson Galang <gerson.galang@versi.edu.au>

'''

from xml.sax import SAXParseException, ContentHandler
from tardis.tardis_portal import metsstruct
from tardis.tardis_portal import models
from tardis.tardis_portal.logger import logger
from django.utils.safestring import SafeUnicode
from xml.sax.handler import feature_namespaces
from xml.sax import make_parser


class MetsDataHolder():
    '''An instance of this class is used by MetsExperimentStructCreator and
    MetsMetadataInfoHandler to pass information between each other.

    '''

    # holds the experiment Id that the DB has provided after the experiment
    # has been saved
    experimentDatabaseId = None

    metadataMap = None
    metsStructMap = None


class MetsExperimentStructCreator(ContentHandler):
    '''The METS document parser which creates the experiment structure before
    the MetsMetadataInfoHandler starts saving the metadata of the experiments,
    datasets, and datafiles in the database.

    '''

    def __init__(self, holder):
        self.holder = holder
        self.experiment = None
        self.inFileGrp = False
        self.processExperimentStruct = False
        self.processDatasetStruct = False
        self.datafile = None
        self.dataset = None
        self.inStructMap = False

        # holds a dictionary of objects (experiment, dataset, datafiles)
        # that contains metadata information. this makes lookup on the objects
        # based on the mets metadata id easier later on when the second parse
        # is done.
        self.metadataMap = {}
        self.metsStructMap = {}

    def startElementNS(self, name, qname, attrs):

        # just get the element name without the namespace
        elName = name[1]

        if elName == 'fileGrp':
            # flag that we are now in the fileGrp element which encapsulates
            # the file listing
            self.inFileGrp = True
            self.datafilesMap = {}

        elif elName == 'file' and self.inFileGrp:
            fileName = _getAttrValueByQName(attrs, 'OWNERID')
            fileId = _getAttrValueByQName(attrs, 'ID')
            fileSize = _getAttrValueByQName(attrs, 'SIZE')
            fileMetadataIds = _getAttrValueByQName(attrs, 'ADMID')

            # instantiate the datafile
            self.datafile = metsstruct.Datafile(
                fileId, fileName, fileSize, fileMetadataIds is not None and
                fileMetadataIds.split() or None)

            # add an entry for this datafile in the metadataMap so we can
            # easily look it up later on when we do our second parse
            if fileMetadataIds is not None:
                for fileMetadataId in fileMetadataIds.split():
                    if self.metadataMap.has_key(fileMetadataId):
                        self.metadataMap[fileMetadataId].append(self.datafile)
                    else:
                        self.metadataMap[fileMetadataId] = [self.datafile]

        elif elName == 'FLocat' and self.inFileGrp and \
                _getAttrValueByQName(attrs, 'LOCTYPE') == 'URL':

            # add the URL info to the datafile
            fileUrl = _getAttrValue(attrs,
                ('http://www.w3.org/1999/xlink', 'href'))
            self.datafile.url = fileUrl

        elif elName == 'structMap':
            self.inStructMap = True

        elif elName == 'div' and \
                self.inStructMap and \
                _getAttrValueByQName(attrs, 'TYPE') == 'investigation':
            # investigation maps to an experiment in the METS world

            self.processExperimentStruct = True

            # instantiate a new experiment
            experimentId = _getAttrValueByQName(attrs, 'DMDID')
            experimentMetadataIds = \
                _getAttrValueByQName(attrs, 'ADMID')
            self.experiment = metsstruct.Experiment(experimentId,
                experimentMetadataIds is not None and
                experimentMetadataIds.split() or None)

            # add an entry for this experiment in the metadataMap so we can
            # easily look it up later on when we do our second parse
            if experimentMetadataIds is not None:
                for experimentMetadataId in experimentMetadataIds.split():
                    if self.metadataMap.has_key(experimentMetadataId):
                        self.metadataMap[
                            experimentMetadataId].append(self.experiment)
                    else:
                        self.metadataMap[experimentMetadataId] = \
                            [self.experiment]

            # we'll save all the div element entries in the metsStructMap so
            # we can easily look them up when we do our second parse
            self.metsStructMap[experimentId] = self.experiment

        elif elName == 'div' and \
                self.processExperimentStruct and \
                _getAttrValueByQName(attrs, 'TYPE') == 'dataset':

            self.processDatasetStruct = True

            # instantiate a new dataset
            datasetId = _getAttrValueByQName(attrs, 'DMDID')
            datasetMetadataIds = _getAttrValueByQName(attrs, 'ADMID')
            self.dataset = metsstruct.Dataset(datasetId,
                datasetMetadataIds is not None and datasetMetadataIds.split()
                or None)

            # we'll also link the newly created dataset with the current
            # experiment
            self.dataset.experiment = self.experiment

            # add an entry for this dataset in the metadataMap so we can
            # easily look it up later on when we do our second parse
            if datasetMetadataIds is not None:
                for datasetMetadataId in datasetMetadataIds.split():
                    if self.metadataMap.has_key(datasetMetadataId):
                        self.metadataMap[
                            datasetMetadataId].append(self.dataset)
                    else:
                        self.metadataMap[datasetMetadataId] = [self.dataset]

            # we'll save all the div element entries in the metsStructMap so
            # we can easily look them up when we do our second parse
            self.metsStructMap[datasetId] = self.dataset

        elif elName == 'fptr' and self.processDatasetStruct:
            fileId = _getAttrValueByQName(attrs, 'FILEID')

            # now that we have the fileId attribute, let's add the actual
            # datafile object from the datafilesMap into the dataset
            self.dataset.datafiles.append(self.datafilesMap[fileId])

            # we'll also need link this datafile with it's dataset holder
            self.datafilesMap[fileId].dataset = self.dataset

    def endElementNS(self, name, qname):

        # just get the element name without the namespace
        elName = name[1]

        if elName == 'fileGrp':
            self.inFileGrp = False

        elif elName == 'file' and self.inFileGrp:
            # save the datafile in the map then reset it to 'None'
            self.datafilesMap[self.datafile.id] = self.datafile
            self.datafile = None

        elif elName == 'structMap':
            # technically, we've finished doing our first pass here.
            # at this point we can assume that we already have the experiment
            # structure available that we can use on our second pass
            self.holder.metsStructMap = self.metsStructMap
            self.holder.metadataMap = self.metadataMap

            self.inStructMap = False

            # let try to have the datafilesMap garbage collected
            self.datafilesMap = None

        elif elName == 'div' and self.processDatasetStruct:

            self.experiment.datasets.append(self.dataset)
            self.dataset = None
            self.processDatasetStruct = False

        elif elName == 'div' and self.processExperimentStruct:

            self.processExperimentStruct = False

    def characters(self, chars):

        # can't think of anything to do in here at the moment...
        pass


class MetsMetadataInfoHandler(ContentHandler):
    '''This parser does the actual database ingestion.

    After the MetsExperimentStructCreator creates the experiment structure,
    this parser goes through the METS document again to look up which file
    the metadata belongs to, links the file and metadata and saves an entry of
    the datafile in the database.

    '''

    def __init__(self, holder, tardisExpId, createdBy):
        self.holder = holder
        self.tardisExpId = tardisExpId
        self.createdBy = createdBy

        self.inDmdSec = False
        self.inName = False
        self.inInstitution = False
        self.inAmdSec = False
        self.inTechMd = False
        self.grabInstitution = False
        self.grabTitle = False
        self.metsObject = None
        self.grabMightBeAuthor = False
        self.grabRoleTerm = False
        self.mightBeAuthor = None
        self.grabExperimentUrl = False

        self.processExperimentStruct = False
        self.processDatasetStruct = False

        self.processMetadata = False
        
        # this will hold the techMD ID
        self.metadataId = None

        self.institution = None
        self.grabAbstract = False

        # a flag to tell if we are now inside techMD's xmlData element
        self.inXmlData = False

        # holds the current direct xmlData child element we are processing
        self.xmlDataChildElement = None

        self.parameterName = None

        # a cache of the current experiment model object we are processing
        self.modelExperiment = None

        # a cache of the current dataset model object we are processing
        self.modelDataset = None

        # a cache of the current datafile being processed
        self.modelDatafile = None

        # this will hold the URI of the experiment/dataset/datafile
        # metadata schema
        self.elementNamespace = None

        # this will be used to temporarily hold the metadata for the
        # experiment, dataset or datafile
        self.tempMetadataHolder = {}

        # holds a quick lookup table of all the instantiated Dataset objects
        # that the new instantiated datafiles will be linked to
        self.datasetLookupDict = {}

        # the custom parser (or handler) to use for the given metadata
        self.customHandler = None

    def startElementNS(self, name, qname, attrs):
        # just get the element name without the namespace
        elName = name[1]

        if elName == 'dmdSec':
            self.inDmdSec = True

            structId = _getAttrValueByQName(attrs, 'ID')
            self.metsObject = self.holder.metsStructMap[structId]

            metsObjectClassName = self.metsObject.__class__.__name__

            if metsObjectClassName == 'Experiment':
                self.processExperimentStruct = True
            elif metsObjectClassName == 'Dataset':
                self.processDatasetStruct = True
            else:
                # we'll definitely have only either Experiment or Dataset
                # object in the metsStructMap, if there are other type of
                # objects that got saved in the map, we'll throw an exception
                raise SAXParseException

        elif elName == 'title' and self.inDmdSec:
            self.grabTitle = True

        elif elName == 'url' and self.processExperimentStruct:
            self.grabExperimentUrl = True

        elif elName == 'abstract' and self.processExperimentStruct:
            self.grabAbstract = True

        elif elName == 'name' and self.processExperimentStruct:
            self.inName = True

        elif elName == 'namePart' and self.inName:
            self.grabMightBeAuthor = True

        elif elName == 'roleTerm' and self.mightBeAuthor is not None:
            self.grabRoleTerm = True

        elif elName == 'agent':
            agentRole = _getAttrValueByQName(attrs, 'ROLE')
            agentType = _getAttrValueByQName(attrs, 'TYPE')
            if agentRole == 'DISSEMINATOR' and agentType == 'ORGANIZATION':
                self.inInstitution = True

        elif elName == 'name' and self.inInstitution:
            self.grabInstitution = True

        elif elName == 'amdSec':
            # let's start processing the metadata info..
            self.inAmdSec = True

        elif elName == 'techMD' and self.inAmdSec:
            self.inTechMd = True
            self.metadataId = _getAttrValueByQName(attrs, 'ID')
            self.processMetadata = True

        elif elName == 'xmlData' and self.inTechMd:
            self.inXmlData = True

        elif self.xmlDataChildElement is None and self.inXmlData:
            self.xmlDataChildElement = elName

            # let's reset the tempMetadataHolder dictionary for this new batch
            # of datafile metadata
            self.tempMetadataHolder = {}
            self.elementNamespace = name[0]

            # let's check if there's a custom parser that we should use for
            # this metadata block (aka parameter set). if there is, use it!
            from tardis.tardis_portal.metshandler import customHandlers
            if self.elementNamespace in customHandlers:
                self.customHandler = customHandlers[self.elementNamespace]
                self.customHandler.resetMetadataDict()

        elif self.customHandler is not None:
            self.customHandler.startElement(elName, attrs)

        elif self.parameterName is None and \
                self.xmlDataChildElement is not None:
            # let's save the metadata field name so we can handle it's value
            # when we see its closing tag...
            self.parameterName = elName

    def endElementNS(self, name, qname):
        # just get the element name without the namespace
        elName = name[1]

        if elName == 'dmdSec':
            self.inDmdSec = False
            # if we currently processing an experiment structure, let's
            # save the institution value before we finalise the experiment
            if self.processExperimentStruct:
                self.metsObject.institution = self.institution

                # let's save the experiment in the DB
                self.modelExperiment = models.Experiment(
                    id=self.tardisExpId,
                    url=self.metsObject.url,
                    approved=True,
                    title=self.metsObject.title,
                    institution_name=self.metsObject.institution,
                    description=self.metsObject.description,
                    created_by=self.createdBy,
                    start_time=None,
                    end_time=None)

                self.modelExperiment.save()

                self.holder.experimentDatabaseId = self.modelExperiment.id

                x = 0
                for author in self.metsObject.authors:
                    try:
                        # check if the given author already exists in the DB
                        author = models.Author.objects.get(
                            name=SafeUnicode(author))
                    except models.Author.DoesNotExist:
                        # create it otherwise
                        author = models.Author(name=SafeUnicode(author))
                        author.save()

                    author_experiment = models.Author_Experiment(
                        experiment=self.modelExperiment,
                        author=author, order=x)
                    author_experiment.save()
                    x = x + 1

            elif self.processDatasetStruct:
                # let's save the dataset in the DB
                self.modelDataset = models.Dataset(
                    experiment=self.modelExperiment,
                    description=self.metsObject.title)
                self.modelDataset.save()

                # let's also save the modelDataset in a dictionary so that we
                # can look it up easily later on when we start processing
                # the datafiles.
                self.datasetLookupDict[self.metsObject.id] = self.modelDataset

            self.metsObject = None

            self.processExperimentStruct = False
            self.processDatasetStruct = False

        elif elName == 'title' and self.inDmdSec:
            self.grabTitle = False

        elif elName == 'url' and self.processExperimentStruct:
            self.grabExperimentUrl = False

        elif elName == 'abstract' and self.processExperimentStruct:
            self.grabAbstract = False

        elif elName == 'name' and self.processExperimentStruct:
            self.inName = False

        elif elName == 'namePart' and self.inName:
            self.grabMightBeAuthor = False

        elif elName == 'roleTerm' and self.inName:
            self.grabRoleTerm = False
            self.mightBeAuthor = None

        elif elName == 'name' and self.inInstitution:
            self.grabInstitution = False

        elif elName == 'agent':
            self.inInstitution = False

        elif elName == 'amdSec':
            # we're done processing the metadata entries
            self.inAmdSec = False

            # let's reset the cached experiment model object
            self.modelExperiment = None

        elif elName == 'techMD' and self.inAmdSec:
            self.inTechMd = False
            self.metadataId = None
            self.metsObject = None
            self.processMetadata = False

        elif elName == 'xmlData' and self.inTechMd:
            self.inXmlData = False

        elif elName != self.xmlDataChildElement and \
                self.customHandler is not None:
            self.customHandler.endElement(elName)

        elif elName == self.xmlDataChildElement and self.inXmlData:

            if self.customHandler is not None:
                self.tempMetadataHolder = self.customHandler.metadataDict

            try:
                schema = models.Schema.objects.get(
                    namespace__exact=self.elementNamespace)

                # get the associated parameter names for the given schema
                parameterNames = \
                    models.ParameterName.objects.filter(
                    schema__namespace__exact=schema.namespace).order_by('id')

                # let's create a trigger holder which we can use to check
                # if we still need to create another parameterset entry in the
                # DB
                createParamSetFlag = {'experiment': True, 'dataset': True, 'datafile': True}
                datasetParameterSet = None
                datafileParameterSet = None

                if self.holder.metadataMap.has_key(self.metadataId):
                    for metsObject in self.holder.metadataMap[self.metadataId]:
                        self.metsObject = metsObject
        
                        metsObjectClassName = self.metsObject.__class__.__name__
            
                        if metsObjectClassName == 'Experiment':
    
                            if createParamSetFlag['experiment']:
                                # create a new parameter set for the metadata
                                parameterSet = \
                                    models.ExperimentParameterSet(schema=schema)
                                parameterSet.save()
            
                                # now let's process the experiment parameters
                                for parameterName in parameterNames:
                                    if self.tempMetadataHolder.has_key(parameterName.name):
                                        parameterValue = self.tempMetadataHolder[
                                            parameterName.name]
                                        if parameterValue != '':
                                            self._saveParameter('ExperimentParameter',
                                                parameterName, parameterValue,
                                                parameterSet)
                                
                                createParamSetFlag['experiment'] = False
        
                                # now link this parameterset with the experiment
                                parameterSet.experiment.add(self.modelExperiment)
                            else:
                                # this is not even allowed as there's only going
                                # to be one experiment per METS file
                                raise Exception('forbidden state!')
    
            
                        elif metsObjectClassName == 'Dataset':
                            if createParamSetFlag['dataset']:
                                # create a new parameter set for the dataset metadata
                                datasetParameterSet = \
                                    models.DatasetParameterSet(schema=schema)
                                datasetParameterSet.save()
            
                                # now let's process the dataset parameters
                                for parameterName in parameterNames:
                                    if self.tempMetadataHolder.has_key(parameterName.name):
                                        parameterValue = self.tempMetadataHolder[
                                            parameterName.name]
                                        if parameterValue != '':
                                            self._saveParameter('DatasetParameter',
                                                parameterName, parameterValue,
                                                datasetParameterSet)
                                
                                # disable creation for the next visit
                                createParamSetFlag['dataset'] = False
    
                            
                            dataset = self.datasetLookupDict[self.metsObject.id]
                            
                            # now link this parameterset with the dataset
                            datasetParameterSet.dataset.add(dataset)
            
                        elif metsObjectClassName == 'Datafile':
                            # this will be a good time to save the "hard" metadata of this
                            # datafile so that when we start adding "soft" metadata
                            # parameters to it, we already have an entry for it in the DB
            
                            # look up the dataset this file belongs to
                            thisFilesDataset = self.datasetLookupDict[
                                self.metsObject.dataset.id]
            
                            # also check if the file already exists
                            datafile = thisFilesDataset.dataset_file_set.filter(
                                filename=self.metsObject.name, size=self.metsObject.size)
            
                            if datafile.count() == 0:
                                self.modelDatafile = models.Dataset_File(
                                    dataset=thisFilesDataset,
                                    filename=self.metsObject.name,
                                    url=self.metsObject.url,
                                    size=self.metsObject.size,
                                    protocol=self.metsObject.url.split('://')[0])
                
                                self.modelDatafile.save()
                            else:
                                self.modelDatafile = thisFilesDataset.dataset_file_set.get(
                                    filename=self.metsObject.name, size=self.metsObject.size)
            
                            # TODO: we need to note here that we are only creating a
                            #       datafile entry in the DB for files that have
                            #       corresponding metadata. if we are to create a file
                            #       entry for files with no metadata, we'll need to
                            #       get the unaccessed datafiles from datasetLookupDict.
    
    
                            if createParamSetFlag['datafile']:
                                # create a new parameter set for the metadata
                                datafileParameterSet = \
                                    models.DatafileParameterSet(schema=schema)
                                datafileParameterSet.save()
            
                                # now let's process the datafile parameters
                                for parameterName in parameterNames:
                                    if self.tempMetadataHolder.has_key(parameterName.name):
                                        parameterValue = self.tempMetadataHolder[
                                            parameterName.name]
                                        if parameterValue != '':
                                            self._saveParameter('DatafileParameter',
                                                parameterName, parameterValue,
                                                datafileParameterSet)
                                createParamSetFlag['datafile'] = False
        
                            # now link this parameterset with the datafile
                            datafileParameterSet.dataset_file.add(self.modelDatafile)
                    

            except models.Schema.DoesNotExist:
                logger.warning('unsupported schema being ingested' +
                    self.elementNamespace)

            # reset the current xmlData child element so that if a new
            # parameter set is read, we can process it again
            self.xmlDataChildElement = None
            self.customHandler = None

        elif elName == self.parameterName and \
                self.xmlDataChildElement is not None:

            # reset self.parameterName to None so the next parameter can be
            # processed
            self.parameterName = None

    def _saveParameter(self, parameterTypeClass, parameterName,
                       parameterValue, parameterSet):
        '''Save the metadata field in the database.

        Reference:
        http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname

        '''
        logger.debug('saving parameter %s: %s' %
            (parameterName, parameterValue))
        if parameterName.is_numeric:
            parameter = \
                getattr(models, parameterTypeClass)(
                parameterset=parameterSet,
                name=parameterName,
                string_value=None,
                numerical_value=float(parameterValue))
        else:
            parameter = \
                getattr(models, parameterTypeClass)(
                parameterset=parameterSet,
                name=parameterName,
                string_value=parameterValue,
                numerical_value=None)
        parameter.save()

    def characters(self, chars):
        if self.processExperimentStruct:

            # handle the different experiment fields
            if self.grabTitle:
                self.metsObject.title = chars
            elif self.grabExperimentUrl:
                self.metsObject.url = chars
            elif self.grabAbstract:
                self.metsObject.description = chars
            elif self.grabMightBeAuthor:
                self.mightBeAuthor = chars

            # if it's really an author, add the mightBeAuthor into the
            # experiment's author list
            elif self.grabRoleTerm and chars == 'author':
                self.metsObject.authors.append(self.mightBeAuthor)

        elif self.grabInstitution:
            self.institution = chars

        elif self.processDatasetStruct:
            if self.grabTitle:
                self.metsObject.title = chars

        elif self.customHandler is not None:
            self.customHandler.characters(chars)

        elif chars.strip() != '' and self.parameterName is not None and \
                self.processMetadata:
            # save the parameter value in the temporary metadata dictionary
            self.tempMetadataHolder[self.parameterName] = chars


def _getAttrValue(attrs, attrName):
    try:
        return attrs.getValue(attrName)
    except KeyError:
        return None


def _getAttrValueByQName(attrs, attrName):
    try:
        return attrs.getValueByQName(attrName)
    except KeyError:
        return None


def parseMets(filename, createdBy, expId=None):
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
