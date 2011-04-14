'''
Created on 16/03/2011

@author: Gerson Galang
'''
from base64 import b64encode
from datetime import datetime
from os.path import abspath, join

from django.conf import settings

from tardis.tardis_portal.models import *
from tardis.tardis_portal.schema.mets import *


class MetsExporter():

    def export(self, experimentId):
       # initialise the metadata counter
        metadataCounter = 1
        experiment = Experiment.objects.get(id=experimentId)

        # TODO: what info do we put on label?
        _mets = mets(PROFILE="Scientific Dataset Profile 1.0", LABEL="",
            TYPE="study", OBJID="A-{0}".format(metadataCounter))

        _amdSec = amdSecType()

        # create a div entry for experiment
        experimentDiv = divType(DMDID="E-1", ADMID="A-{0}".format(
            metadataCounter), TYPE="investigation")

        parameterSets = ExperimentParameterSet.objects.filter(
            experiment=experiment)

        experimentMdWrap = mdWrap(MDTYPE="OTHER",
            OTHERMDTYPE="TARDISEXPERIMENT")
        if parameterSets.count() > 0:
            _xmlData = self.getTechMDXmlDataForParameterSets(
                parameterSets, "experiment")
            experimentMdWrap.set_xmlData(_xmlData)

        # create an amdSec entry for the experiment
        _techMD = mdSecType(ID="A-{0}".format(metadataCounter),
            mdWrap=experimentMdWrap)
        _amdSec = amdSecType()
        _amdSec.add_techMD(_techMD)

        _xmlData = self.getDmdSecXmlDataForExperiment(
            experiment, "http://www.loc.gov./mods/v3")
        experimentMdWrap = mdWrap(MDTYPE="MODS", xmlData=_xmlData)
        _dmdSec = mdSecType(ID="E-1", mdWrap=experimentMdWrap)

        _mets.add_dmdSec(_dmdSec)
        _mets.add_amdSec(_amdSec)

        metadataCounter += 1

        _structMap = structMapType(TYPE="logical", div=experimentDiv)

        datasets = Dataset.objects.filter(experiment=experiment)

        _fileGrp = fileGrpType(USE='original')
        _fileSec = fileSec()
        _fileSec.add_fileGrp(_fileGrp)

        fileCounter = 1
        datasetCounter = 1
        for dataset in datasets:

            # create a div entry for dataset
            datasetDiv = divType(DMDID="D-{0}".format(
                datasetCounter), ADMID="A-{0}".format(metadataCounter),
                TYPE="dataset")

            parameterSets = DatasetParameterSet.objects.filter(dataset=dataset)

            datasetMdWrap = mdWrap(MDTYPE="OTHER", OTHERMDTYPE="TARDISDATASET")
            if parameterSets.count() > 0:
                _xmlData = self.getTechMDXmlDataForParameterSets(
                    parameterSets, "dataset")
                datasetMdWrap.set_xmlData(_xmlData)

            # create an amdSec entry for the experiment
            _techMD = mdSecType(ID="A-{0}".format(metadataCounter),
                mdWrap=datasetMdWrap)
            _amdSec.add_techMD(_techMD)

            _xmlData = self.getDmdSecXmlDataForDataset(
                dataset, "http://www.loc.gov./mods/v3")
            datasetMdWrap = mdWrap(MDTYPE="MODS", xmlData=_xmlData)
            _dmdSec = mdSecType(ID="D-{0}".format(datasetCounter),
                mdWrap=experimentMdWrap)
            _mets.add_dmdSec(_dmdSec)

            datasetCounter += 1
            metadataCounter += 1

            experimentDiv.add_div(datasetDiv)

            datafiles = Dataset_File.objects.filter(dataset=dataset)

            for datafile in datafiles:
                # add entry to fileSec
                _file = fileType(ID="F-{0}".format(fileCounter),
                    MIMETYPE=(datafile.mimetype or "application/octet-stream"),
                    SIZE=datafile.size, CHECKSUM=(datafile.md5sum or
                    "application/octet-stream"), CHECKSUMTYPE="MD5",
                    OWNERID=datafile.filename, ADMID="A-{0}".format(
                    metadataCounter))
                _file.add_FLocat(FLocat(LOCTYPE="URL", href=datafile.url,
                    type_="simple"))
                _fileGrp.add_file(_file)

                # add entry to structMap
                datasetDiv.add_fptr(fptr(FILEID="F-{0}".format(fileCounter)))
                parameterSets = DatafileParameterSet.objects.filter(
                    dataset_file=datafile)

                datafileMdWrap = mdWrap(MDTYPE="OTHER",
                    OTHERMDTYPE="TARDISDATAFILE")
                if parameterSets.count() > 0:
                    _xmlData = self.getTechMDXmlDataForParameterSets(
                        parameterSets, "datafile")
                    datafileMdWrap.set_xmlData(_xmlData)

                # create an amdSec entry for the experiment
                _techMD = mdSecType(ID="A-{0}".format(metadataCounter),
                    mdWrap=datafileMdWrap)
                _amdSec.add_techMD(_techMD)

                fileCounter += 1
                metadataCounter += 1
        _mets.add_structMap(_structMap)
        _mets.set_fileSec(_fileSec)

        # create teh mets header
        dateNow = datetime.now().isoformat(' ').replace(
            ' ', 'T').rsplit('.')[0]
        _metsHdr = metsHdr(CREATEDATE=dateNow, LASTMODDATE=dateNow)
        institution = agent(TYPE="ORGANIZATION", ROLE="DISSEMINATOR",
            name=experiment.institution_name)
        creator = agent(TYPE="OTHER", ROLE="CREATOR",
            name="METS Exporter 0.1")
        _metsHdr.add_agent(institution)
        _metsHdr.add_agent(creator)

        _mets.set_metsHdr(_metsHdr)

        filename = join(experiment.get_or_create_directory(),
                        'mets_expid_%s.xml' % str(experiment.id))
        outfile = open(filename, 'w')
        _mets.export(outfile=outfile, level=1)
        outfile.close()
        return filename

    def getTechMDXmlDataForParameterSets(self, parameterSets, type="experiment"):

        _xmlData = xmlData()
        for parameterSet in parameterSets:
            paramObj = ExperimentParameter
            if type == "experiment":
                elementName = "experiment"
                paramObj = ExperimentParameter
            elif type == "dataset":
                elementName = "dataset"
                paramObj = DatasetParameter
            else:
                elementName = "datafile"
                paramObj = DatafileParameter

            parameters = paramObj.objects.filter(parameterset=parameterSet)

            metadataDict = {}
            for parameter in parameters:
                # print parameter.name
                if parameter.name.data_type is ParameterName.NUMERIC:
                    metadataDict[parameter.name.name] = \
                        str(parameter.numerical_value) or 'None'

                elif parameter.name.data_type is ParameterName.FILENAME and \
                        parameter.name.units.startswith('image'):

                    # encode image as b64
                    expid = parameter.getExpId()
                    file_path = abspath(join(settings.FILE_STORE_PATH,
                                             str(expid),
                                             parameter.string_value))
                    metadataDict[parameter.name.name] = \
                        b64encode(open(file_path).read()) or 'None'
                else:
                    metadataDict[parameter.name.name] = \
                        parameter.string_value.strip() or 'None'

            _xmlData.add_xsdAny_(self.createXmlDataContentForParameterSets(
                elementName=elementName,
                schemaURI=parameterSet.schema.namespace,
                metadataDict=metadataDict))

        return _xmlData

    def createXmlDataContentForParameterSets(self, elementName, schemaURI="",
            metadataDict={}):
        """
        elName - can be experiment, dataset, datafile or something else
        schemaURI - URI of the schema
        metadataDict - a dictionary of the metadata fields where key is the
            name of the field while the value is the value of the field.
        """
        import elementtree.ElementTree as ET
        ET._namespace_map[schemaURI] = "tardis"

        # build a tree structure
        xmlDataContentEl = ET.Element(elementName)

        for k, v in metadataDict.iteritems():
            metadataField = ET.SubElement(xmlDataContentEl, k)
            metadataField.text = v
        return xmlDataContentEl

    def getDmdSecXmlDataForExperiment(self, experiment, schemaURI):
        import elementtree.ElementTree as ET
        ET._namespace_map[schemaURI] = "mods"

        # build a tree structure
        xmlDataContentEl = ET.Element("mods")

        titleInfo = ET.SubElement(xmlDataContentEl, "titleInfo")
        title = ET.SubElement(titleInfo, "title")
        title.text = experiment.title

        genre = ET.SubElement(xmlDataContentEl, "genre")
        genre.text = "experiment"

        relatedItem = ET.SubElement(xmlDataContentEl, "relatedItem",
            {"type": "otherVersion"})
        originInfo = ET.SubElement(relatedItem, "originInfo")
        publisher = ET.SubElement(originInfo, "publisher")
        publisher.text = "Primary Citation"
        location = ET.SubElement(relatedItem, "location")
        location.text = experiment.url

        abstract = ET.SubElement(xmlDataContentEl, "abstract")
        abstract.text = experiment.description

        authors = Author_Experiment.objects.filter(experiment=experiment)
        for author in authors:
            name = ET.SubElement(xmlDataContentEl, "name",
                {"type": "personal"})
            namePart = ET.SubElement(name, "namePart")
            namePart.text = author.author
            role = ET.SubElement(name, "role")
            roleTerm = ET.SubElement(role, "roleTerm", {"type": "text"})
            roleTerm.text = "author"

        # TODO: figure out where I could get the PDB details

        _xmlData = xmlData()
        _xmlData.add_xsdAny_(xmlDataContentEl)
        return _xmlData

    def getDmdSecXmlDataForDataset(self, dataset, schemaURI):
        import elementtree.ElementTree as ET
        ET._namespace_map[schemaURI] = "mods"

        # build a tree structure
        xmlDataContentEl = ET.Element("mods")

        titleInfo = ET.SubElement(xmlDataContentEl, "titleInfo")
        title = ET.SubElement(titleInfo, "title")
        title.text = dataset.description

        # TODO: figure out where I could get the PDB details
        _xmlData = xmlData()
        _xmlData.add_xsdAny_(xmlDataContentEl)
        return _xmlData

exporter = MetsExporter()
