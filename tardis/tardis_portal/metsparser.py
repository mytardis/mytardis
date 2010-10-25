'''
The METS document parser.

@author: Gerson Galang
'''

from xml.sax import SAXParseException, ContentHandler
from tardis.tardis_portal import metsstruct
from tardis.tardis_portal import models
from tardis.tardis_portal.logger import logger
from django.utils.safestring import SafeUnicode


class MetsDataHolder():
    '''An instance of this class is used by MetsExperimentStructCreator and
    MetsMetadataInfoHandler to pass information between each other.

    '''

    # holds the experiment Id that the DB has provided after the experiment
    # has been saved
    experimentDatabaseId = None

    experiments = None
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
        self.experiments = []
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
            #print attrs.getNames()
            fileName = _getAttrValueByQName(attrs, 'OWNERID')
            fileId = _getAttrValueByQName(attrs, 'ID')
            fileSize = _getAttrValueByQName(attrs, 'SIZE')
            fileMetadataId = _getAttrValueByQName(attrs, 'ADMID')

            # instantiate the datafile
            self.datafile = metsstruct.Datafile(
                fileId, fileName, fileSize, fileMetadataId)

            # add an entry for this datafile in the metadataMap so we can
            # easily look it up later on when we do our second parse
            if fileMetadataId is not None:
                self.metadataMap[fileMetadataId] = self.datafile

        elif elName == 'FLocat' and self.inFileGrp and \
                _getAttrValueByQName(attrs, 'LOCTYPE') == 'URL':

            # add the URL info to the datafile
            fileUrl = _getAttrValue(attrs, ('http://www.w3.org/1999/xlink', 'href'))
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
            experimentMetadataId = \
                _getAttrValueByQName(attrs, 'ADMID')
            self.experiment = metsstruct.Experiment(experimentId,
                experimentMetadataId)

            # add an entry for this experiment in the metadataMap so we can
            # easily look it up later on when we do our second parse
            if experimentMetadataId is not None:
                self.metadataMap[experimentMetadataId] = self.experiment

            # we'll save all the div element entries in the metsStructMap so
            # we can easily look them up when we do our second parse
            self.metsStructMap[experimentId] = self.experiment

        elif elName == 'div' and \
                self.processExperimentStruct and \
                _getAttrValueByQName(attrs, 'TYPE') == 'dataset':

            self.processDatasetStruct = True

            # instantiate a new dataset
            datasetId = _getAttrValueByQName(attrs, 'DMDID')
            datasetMetadataId = _getAttrValueByQName(attrs, 'ADMID')
            self.dataset = metsstruct.Dataset(datasetId, datasetMetadataId)

            # we'll also link the newly created dataset with the current
            # experiment
            self.dataset.experiment = self.experiment

            # add an entry for this dataset in the metadataMap so we can
            # easily look it up later on when we do our second parse
            if datasetMetadataId is not None:
                self.metadataMap[datasetMetadataId] = self.dataset

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
            self.holder.experiments = self.experiments
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

            self.experiments.append(self.experiment)
            self.experiment = None
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

        self.processExperimentMetadata = False
        self.processDatasetMetadata = False
        self.processDatafileMetadata = False

        self.institution = None
        self.grabAbstract = False

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
            metadataId = _getAttrValueByQName(attrs, 'ID')
            self.metsObject = self.holder.metadataMap[metadataId]

            metsObjectClassName = self.metsObject.__class__.__name__

            if metsObjectClassName == 'Datafile':
                # this will be a good time to save the "hard" metadata of this
                # datafile so that when we start adding "soft" metadata
                # parameters to it, we already have an entry for it in the DB

                # look up the dataset this file belongs to
                thisFilesDataset = self.datasetLookupDict[
                    self.metsObject.dataset.id]

                self.modelDatafile = models.Dataset_File(
                    dataset=thisFilesDataset,
                    filename=self.metsObject.name,
                    url=self.metsObject.url,
                    size=self.metsObject.size,
                    protocol=self.metsObject.url.split('://')[0])

                self.modelDatafile.save()

                # TODO: we need to note here that we are only creating a
                #       datafile entry in the DB for files that have
                #       corresponding metadata. if we are to create a file
                #       entry for files with no metadata, we'll need to
                #       get the unaccessed datafiles from datasetLookupDict.

        elif elName == 'experiment' and self.inTechMd:
            self.processExperimentMetadata = True

            # let's reset the tempMetadataHolder dictionary for this new batch
            # of experiment metadata
            self.tempMetadataHolder = {}

            self.elementNamespace = name[0]

        elif elName == 'dataset' and self.inTechMd:
            self.processDatasetMetadata = True

            # let's reset the tempMetadataHolder dictionary for this new batch
            # of dataset metadata
            self.tempMetadataHolder = {}

            self.elementNamespace = name[0]

        elif elName == 'datafile' and self.inTechMd:
            self.processDatafileMetadata = True

            # let's reset the tempMetadataHolder dictionary for this new batch
            # of datafile metadata
            self.tempMetadataHolder = {}

            self.elementNamespace = name[0]

        elif self.parameterName is None and \
                (self.processExperimentMetadata or \
                self.processDatasetMetadata or \
                self.processDatafileMetadata):
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
                    created_by=self.createdBy)

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
            self.metsObject = None

        elif self.inTechMd and (elName == 'experiment' or \
                elName == 'dataset' or elName == 'datafile'):
            try:
                schema = models.Schema.objects.get(
                    namespace__exact=self.elementNamespace)

                # get the associated parameter names for the given schema
                parameterNames = \
                    models.ParameterName.objects.filter(
                    schema__namespace__exact=schema.namespace).order_by('id')

                if elName == 'experiment':

                    # create a new parameter set for the metadata
                    parameterSet = \
                        models.ExperimentParameterSet(
                        schema=schema, experiment=self.modelExperiment)

                    parameterSet.save()

                    # now let's process the experiment experiment parameters
                    for parameterName in parameterNames:
                        try:
                            parameterValue = self.tempMetadataHolder[
                                parameterName.name]
                            if parameterValue != '':
                                self._saveParameter('ExperimentParameter',
                                    parameterName, parameterValue,
                                    parameterSet)
                        except KeyError:
                            # we'll just pass as we don't really need to deal
                            # with the current parameterName which is not
                            # provided in the current section of the METS
                            # document
                            pass

                    self.processExperimentMetadata = False

                elif elName == 'dataset':

                    # create a new parameter set for the dataset metadata
                    parameterSet = \
                        models.DatasetParameterSet(
                        schema=schema, dataset=self.modelDataset)
                    parameterSet.save()

                    # now let's process the experiment parameters
                    for parameterName in parameterNames:
                        try:
                            parameterValue = self.tempMetadataHolder[
                                parameterName.name]
                            if parameterValue != '':
                                self._saveParameter('DatasetParameter',
                                    parameterName, parameterValue,
                                    parameterSet)
                        except KeyError:
                            # we'll just pass as we don't really need to deal
                            # with the current parameterName which is not
                            # provided in the current section of the METS
                            # document
                            logger.debug(str(parameterName) +
                                ' is not in the tempMetadataHolder')
                            pass

                    self.processDatasetMetadata = False

                elif elName == 'datafile':

                    # create a new parameter set for the metadata
                    parameterSet = \
                        models.DatafileParameterSet(
                        schema=schema, dataset_file=self.modelDatafile)
                    parameterSet.save()

                    # now let's process the experiment parameters
                    for parameterName in parameterNames:
                        try:
                            parameterValue = self.tempMetadataHolder[
                                parameterName.name]
                            if parameterValue != '':
                                self._saveParameter('DatafileParameter',
                                    parameterName, parameterValue,
                                    parameterSet)
                        except KeyError:
                            # we'll just pass as we don't really need to deal
                            # with the current parameterName which is not
                            # provided in the current section of the METS
                            # document
                            pass

                    self.processDatafileMetadata = False

            except models.Schema.DoesNotExist:
                logger.warning('unsupported schema being ingested' +
                    self.elementNamespace)

        elif elName == self.parameterName and \
                (self.processExperimentMetadata or \
                self.processDatasetMetadata or \
                self.processDatafileMetadata):

            # reset self.parameterName to None so the next parameter can be
            # processed
            self.parameterName = None

    def _saveParameter(self, parameterTypeClass, parameterName,
                       parameterValue, parameterSet):
        '''Save the metadata field in the database.

        Reference:
        http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname

        '''

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
            if self.grabExperimentUrl:
                self.metsObject.url = chars
            if self.grabAbstract:
                self.metsObject.description = chars
            if self.grabMightBeAuthor:
                self.mightBeAuthor = chars

            # if it's really an author, add the mightBeAuthor into the
            # experiment's author list
            if self.grabRoleTerm and chars == 'author':
                self.metsObject.authors.append(self.mightBeAuthor)

        if self.grabInstitution:
            self.institution = chars

        if self.processDatasetStruct:
            if self.grabTitle:
                self.metsObject.title = chars

        if self.parameterName is not None and \
                (self.processExperimentMetadata or \
                self.processDatasetMetadata or \
                self.processDatafileMetadata):

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
