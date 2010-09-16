#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from lxml import etree
from StringIO import StringIO
from django.utils.safestring import SafeUnicode
from tardis.tardis_portal.logger import logger


class ExperimentParser:

    __schema_mods = ('mods', 'http://www.loc.gov/mods/v3')
    __schema_mets = ('METS', 'http://www.loc.gov/METS/')
    __schema_xlink = ('xlink', 'http://www.w3.org/1999/xlink')

    __xpath_findModsElement = \
        "//METS:dmdSec[//METS:div[@TYPE='investigation']/@DMDID = @ID]" \
        "/METS:mdWrap[@MDTYPE='MODS']"
    __xpath_findDivElementWithTypeInvestigation = \
        "//METS:structMap/METS:div[@TYPE='investigation']"
    __xpath_findFileGroup = '//METS:fileSec/METS:fileGrp'

    def __init__(self, xmlString):
        self.tree = etree.parse(StringIO(xmlString))
        logger.debug('(Initializing %s)' % self.tree)

    def __getSingleResult(self, elements):
        if len(elements) == 1:

            # let's reformat the element value that is not in a continuous line
            import os
            return self.__removeLineSeparators(SafeUnicode(elements[0]))
        else:
            return None

    def __removeLineSeparators(self, str):
        """Remove all the line separators and whitespaces from the given
        string.

        """

        return ' '.join([l.strip() for l in str.splitlines()]).strip()

    def __getStrippedElements(self, elements):
        """Strip the extra whitespaces (eg '\t', ' ', '\n', etc) at the front
        and back of each of the elements.

        """

        return [e.strip() for e in elements]

    def getTitle(self):
        elements = self.tree.xpath(self.__xpath_findModsElement +
                                   '//mods:title/text()',
                                   namespaces=dict([self.__schema_mods,
                                   self.__schema_mets]))
        return self.__getSingleResult(elements)

    def getAuthors(self):
        elements = self.tree.xpath(self.__xpath_findModsElement +
                                   '//mods:name/mods:namePart/text()',
                                   namespaces=dict([self.__schema_mods,
                                   self.__schema_mets]))
        return self.__getStrippedElements(elements)

    def getAbstract(self):
        elements = self.tree.xpath(self.__xpath_findModsElement +
                                   '//mods:abstract/text()',
                                   namespaces=dict([self.__schema_mods,
                                   self.__schema_mets]))
        return self.__getSingleResult(elements)

    def getRelationURLs(self):
        elements = self.tree.xpath(self.__xpath_findModsElement +
                                   '//mods:url/text()',
                                   namespaces=dict([self.__schema_mods,
                                   self.__schema_mets]))
        return self.__getStrippedElements(elements)

    def getAgentName(self, role):
        elements = self.tree.xpath("//METS:metsHdr/METS:agent[@ROLE='" +
                                   role + "']/METS:name/text()",
                                   namespaces=dict([self.__schema_mods,
                                   self.__schema_mets]))
        return self.__getSingleResult(elements)

    def getDatasetTitle(self, dataset_id):
        elements = self.tree.xpath("//METS:dmdSec[@ID='" + dataset_id +
                                   "']/METS:mdWrap[@MDTYPE='MODS']" +
                                   '//mods:title/text()',
                                   namespaces=dict([self.__schema_mods,
                                   self.__schema_mets]))
        return self.__getSingleResult(elements)

    def getDatasetDMDIDs(self):
        """Get the IDs of the all the datasets of this experiment."""

        elements = \
            self.tree.xpath(self.__xpath_findDivElementWithTypeInvestigation +
                            "//METS:div[@TYPE='dataset']" + '/@DMDID',
                            namespaces=dict([self.__schema_mets]))
        return self.__getStrippedElements(elements)

    def getDatasetADMIDs(self, dataset_id):
        """Get the metadata IDs for the given dataset."""

        elements = \
            self.tree.xpath(self.__xpath_findDivElementWithTypeInvestigation +
                            "//METS:div[@TYPE='dataset' and @DMDID='" +
                            dataset_id + "']/@ADMID",
                            namespaces=dict([self.__schema_mets]))
        return self.__getStrippedElements(elements)

    def getFileIDs(self, dataset_id):
        """Get the list of IDs of files for the given dataset."""

        elements = self.tree.xpath("//METS:div[@DMDID='" + dataset_id +
                                   "']" + '//METS:fptr/@FILEID',
                                   namespaces=dict([self.__schema_mets]))
        return self.__getStrippedElements(elements)

    def getFileLocation(self, file_id):
        elements = \
            self.tree.xpath("//METS:fileSec/METS:fileGrp/METS:file[@ID='" +
                            file_id + "']" + '/METS:FLocat/@xlink:href',
                            namespaces=dict([self.__schema_xlink,
                            self.__schema_mets]))
        return self.__getSingleResult(elements)

    def getFileADMIDs(self, file_id):
        """Get the metadata IDs for the given file."""

        elements = self.tree.xpath(self.__xpath_findFileGroup +
                                   "/METS:file[@ID='" + file_id +
                                   "']/@ADMID",
                                   namespaces=dict([self.__schema_mets]))
        return self.__getStrippedElements(elements)

    def getFileName(self, file_id):
        """Get the filename for the given file_id."""

        elements = self.tree.xpath(self.__xpath_findFileGroup +
                                   "/METS:file[@ID='" + file_id +
                                   "']/@OWNERID",
                                   namespaces=dict([self.__schema_mets]))
        return self.__getSingleResult(elements)

    def getFileSize(self, file_id):
        elements = self.tree.xpath(self.__xpath_findFileGroup +
                                   "/METS:file[@ID='" + file_id +
                                   "']/@SIZE",
                                   namespaces=dict([self.__schema_mets]))
        return self.__getSingleResult(elements)

    def getTechXML(self, tech_id):
        """Get the datafile element which holds the metadata for the file given
        the metadata ID.

        Arguments:
        tech_id -- the metadata ID

        Returns:
        The datafile element which holds the metadata for the file given the
        metadata ID.

        """

        f = StringIO("<?xml version='1.0' ?>"
                     + "<xsl:stylesheet version='2.0' xmlns:xsl='"
                     + "http://www.w3.org/1999/XSL/Transform' "
                     + "xmlns:mets='http://www.loc.gov/METS/'>"
                     + "<xsl:output method='xml' indent='yes'/>"
                     + "<xsl:template match='/'>"
                     + '<xsl:copy-of select="//mets:techMD[@ID=\''
                     + tech_id + '\']/mets:mdWrap/mets:xmlData/*"/>'
                     + '</xsl:template></xsl:stylesheet>')
        xslt_doc = etree.parse(f)
        transform = etree.XSLT(xslt_doc)
        result_tree = transform(self.tree)
        return result_tree

    def getParameterFromTechXML(self, tech_xml, parameter_name):
        prefix = tech_xml.getroot().prefix
        xmlns = tech_xml.getroot().nsmap[prefix]

        parameter_string = ''
        for parameter in parameter_name.split('/'):
            parameter_string = parameter_string + '/' + prefix + ':' \
                + parameter

        elements = tech_xml.xpath('/' + parameter_string + '/text()',
                                  namespaces={prefix: xmlns})
        return self.__getSingleResult(elements)
