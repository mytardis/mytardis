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

from StringIO import StringIO
from lxml import etree

from xml.dom.minidom import parseString
import urllib

from django.utils.safestring import SafeUnicode

from tardis.tardis_portal.models import *
from tardis.tardis_portal.logger import logger


def getText(nodelist):
    rc = ''
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


def getSingleResult(elements):
    if len(elements) == 1:
        return SafeUnicode(elements[0])
    else:
        return None


def getParameterFromTechXML(tech_xml, parameter_name):
    prefix = tech_xml.getroot().prefix
    xmlns = tech_xml.getroot().nsmap[prefix]

    parameter_string = ''
    for parameter in parameter_name.split('/'):
        parameter_string = parameter_string + '/' + prefix + ':' \
            + parameter

    elements = tech_xml.xpath('/' + parameter_string + '/text()',
                              namespaces={prefix: xmlns})

    # logger.debug(elements)
    return getSingleResult(elements)


def getTechXMLFromRaw(md):
    return etree.parse(StringIO(md))


def getXmlnsFromTechXMLRaw(md):
    tech_xml = etree.parse(StringIO(md))
    prefix = tech_xml.getroot().prefix
    xmlns = tech_xml.getroot().nsmap[prefix]

    return xmlns


class ProcessExperiment:

    def __init__(self):
        pass

    def __call__(self):
        pass

    def download_xml(self, url):
        f = urllib.urlopen(url)
        xmlString = f.read()

        return xmlString

    def null_check(self, string):
        if string == 'null':
            return None
        else:
            return string

    # this is the worst code of all time :) -steve
    def process_simple(self, filename, created_by, eid):

        f = open(filename)
        e = 0
        ds = 0
        df = 0
        current = None
        current_df_id = 0
        mdelist = []

        for line in f:
            line = line.strip()

            # logger.debug("LINE: %s, CURRENT: %s"  % (line, current))
            if line.startswith('<experiment>'):
                current = 'experiment'
                e += 1
                ds = 0
                df = 0
                # initialize with empty strings to avoid key errors
                exp = {}
                exp['abstract'] = ''
                exp['organization'] = ''
                exp['title'] = ''
                exp['url'] = ''
                exp['starttime'] = None
                exp['endtime'] = None
                authors = list()

            elif line.startswith('<dataset>'):

                # commit any experiment if current = experiment
                if current == 'experiment':

                    if eid:
                        experiment = Experiment.objects.get(pk=eid)
                    else:
                        experiment = Experiment()

                    experiment.url = exp['url']
                    experiment.title = exp['title']
                    experiment.institution_name = exp['organization']
                    experiment.description = exp['abstract']
                    experiment.created_by = created_by
                    experiment.start_time = exp['starttime']
                    experiment.end_time = exp['endtime']
                    experiment.save()

                    author_experiments = \
                        Author_Experiment.objects.all()
                    author_experiments = \
                        author_experiments.filter(
                        experiment=experiment).delete()

                    x = 0
                    for authorName in authors:
                        author_experiment = \
                            Author_Experiment(experiment=experiment,
                                author=authorName, order=x)
                        author_experiment.save()
                        x = x + 1

                    experiment.dataset_set.all().delete()

                    if 'metadata' in exp:
                        for md in exp['metadata']:
                            xmlns = getXmlnsFromTechXMLRaw(md)
                            logger.debug('schema %s' % xmlns)
                            schema = None
                            try:
                                schema = Schema.objects.get(
                                    namespace__exact=xmlns)
                            except Schema.DoesNotExist, e:
                                logger.debug('schema not found: ' + e)

                            if schema:
                                parameternames = \
                                    ParameterName.objects.filter(
                                schema__namespace__exact=schema.namespace)

                                parameternames = \
                                    parameternames.order_by('id')

                                tech_xml = getTechXMLFromRaw(md)

                                parameterset = \
                                    ExperimentParameterSet(
                                    schema=schema, experiment=experiment)

                                parameterset.save()

                                for pn in parameternames:
                                    # logger.debug("finding parameter %s in metadata" % pn.name)
                                    try:
                                        if pn.data_type == ParameterName.NUMERIC:
                                            value = \
                                                getParameterFromTechXML(
                                                tech_xml, pn.name)

                                            if value != None:
                                                ep = \
                                                    ExperimentParameter(
                                            parameterset=parameterset,
                                                    name=pn,
                                                    string_value=None,
                                            numerical_value=float(value))
                                                ep.save()
                                        else:
                                            ep = \
                                                ExperimentParameter(
                                                parameterset=parameterset,
                                                name=pn,
                                    string_value=getParameterFromTechXML(
                                                tech_xml, pn.name),
                                                numerical_value=None)
                                            ep.save()
                                    except e:
                                        logger.debug(
                                            'error saving experiment ' +
                                            'parameter: ' + e)

                current = 'dataset'
                ds = ds + 1
                mdflist = []
                mdslist = []
                df = 0
                dataset = dict()

            elif line.startswith('<file>'):

                if current == 'dataset':
                    d = Dataset(experiment=experiment,
                            description=dataset['description'])
                    d.save()

                    if 'metadata' in dataset:
                        for md in dataset['metadata']:
                            if 'metadata' in dataset:
                                xmlns = getXmlnsFromTechXMLRaw(md)

                                logger.debug(
                                    'trying to find parameters with ' +
                                    'an xmlns of ' + xmlns)

                                schema = None
                                try:
                                    schema = \
                                        Schema.objects.get(
                                        namespace__exact=xmlns)
                                except Schema.DoesNotExist, e:
                                    logger.debug('schema not found: ' + e)

                                if schema:
                                    parameternames = \
                                        ParameterName.objects.filter(
                                schema__namespace__exact=schema.namespace)

                                    parameternames = \
                                        parameternames.order_by('id')

                                    tech_xml = \
                                        getTechXMLFromRaw(md)

                                    parameterset = \
                                        DatasetParameterSet(
                                        schema=schema, dataset=d)

                                    parameterset.save()

                                    for pn in parameternames:
                                        logger.debug(
                                            "finding parameter " +
                                            pn.name + " in metadata")
                                        try:
                                            if pn.data_type == ParameterName.NUMERIC:
                                                value = \
                                                getParameterFromTechXML(
                                                    tech_xml, pn.name)

                                                if value != None:
                                                    dp = \
                                                        DatasetParameter(
                                                parameterset=parameterset,
                                                        name=pn,
                                                        string_value=None,
                                            numerical_value=float(value))
                                                    dp.save()
                                            else:
                                                dp = \
                                                    DatasetParameter(
                                                parameterset=parameterset,
                                                    name=pn,
                                    string_value=getParameterFromTechXML(
                                                    tech_xml, pn.name),
                                                    numerical_value=None)
                                                dp.save()
                                        except e:
                                            logger.debug(
                                                'error saving ' +
                                                'experiment parameter: ' +
                                                e)
                else:
                    if self.null_check(datafile['name']):
                        filename = datafile['name']
                    else:
                        filename = datafile['path']

                    url = datafile['path']
                    protocol = datafile['path'].partition('://')[0]
                    if protocol in ['file', 'http', 'https']:
                        protocol = ''

                    dfile = Dataset_File(dataset=d,
                                         filename=filename,
                                         url=url,
                                         size=datafile['size'],
                                         protocol=protocol)
                    dfile.save()
                    current_df_id = dfile.id

                    for md in datafile['metadata']:
                        xmlns = getXmlnsFromTechXMLRaw(md)

                        try:
                            schema = \
                                Schema.objects.get(namespace__exact=xmlns)

                            parameternames = \
                                ParameterName.objects.filter(
                                schema__namespace__exact=schema.namespace)
                            parameternames = \
                                parameternames.order_by('id')

                            tech_xml = getTechXMLFromRaw(md)

                            parameterset = \
                                DatafileParameterSet(schema=schema,
                                dataset_file=dfile)

                            parameterset.save()

                            for pn in parameternames:
                                try:

                                    # print "finding parameter " +
                                    #     pn.name + " in metadata"

                                    dfile = \
                                        Dataset_File.objects.get(
                                        pk=current_df_id)
                                    if pn.data_type == ParameterName.NUMERIC:
                                        value = getParameterFromTechXML(
                                            tech_xml, pn.name)
                                        if value != None:
                                            dp = \
                                                DatafileParameter(
                                                parameterset=parameterset,
                                                name=pn,
                                                string_value=None,
                                            numerical_value=float(value))

                                            dp.save()
                                    else:
                                        dp = \
                                            DatafileParameter(
                                            parameterset=parameterset,
                                            name=pn,
                                    string_value=getParameterFromTechXML(
                                            tech_xml,
                                            pn.name), numerical_value=None)
                                        dp.save()
                                except e:
                                    logger.debug('error saving ' +
                                        'experiment parameter: ' + e)
                        except Schema.DoesNotExist, e:
                            logger.debug('schema not found: ' + e)

                # commit any dataset if current = dataset

                current = 'file'
                df = df + 1
                mdflist = []
                datafile = dict()
                logger.debug('experiment: ' + str(e) + ' dataset: ' +
                    str(ds) + ' datafile: ' + str(df))

            elif line.startswith('<metadata'):

                md = ''
                while line.strip() != '</metadata>':
                    line = f.next()
                    if line.strip() != '</metadata>':
                        md = md + line
                if current == 'file':
                    mdflist.append(md)
                    datafile['metadata'] = mdflist
                elif current == 'experiment':
                    mdelist.append(md)
                    exp['metadata'] = mdelist
                else:
                    mdslist.append(md)
                    dataset['metadata'] = mdslist
            elif line.startswith('<abstract'):

                ab = line.partition('<abstract>')[2]
                while not line.strip().endswith('</abstract>'):
                    line = f.next()
                    ab = ab + line.partition('</abstract>')[0]
                exp['abstract'] = ab

            elif line.startswith('</experiment>'):

                if current == 'dataset':
                    d = Dataset(experiment=experiment,
                            description=dataset['description'])
                    d.save()
                else:

                    if self.null_check(datafile['name']):
                        filename = datafile['name']
                    else:
                        filename = datafile['path']

                    url = datafile['path']
                    protocol = url.partition('://')[0]
                    if protocol in  ['file', 'http', 'https']:
                        protocol = ''

                    dfile = Dataset_File(dataset=d,
                                         filename=filename,
                                         url=url,
                                         size=datafile['size'],
                                         protocol=protocol)
                    dfile.save()

                    current_df_id = dfile.id

                    if 'metadata' in datafile:
                        for md in datafile['metadata']:
                            xmlns = getXmlnsFromTechXMLRaw(md)

                            try:
                                schema = \
                                    Schema.objects.get(
                                    namespace__exact=xmlns)

                                parameternames = \
                                    ParameterName.objects.filter(
                                schema__namespace__exact=schema.namespace)

                                parameternames = \
                                    parameternames.order_by('id')

                                tech_xml = getTechXMLFromRaw(md)

                                parameterset = DatafileParameterSet(
                                    schema=schema, dataset_file=dfile)

                                parameterset.save()

                                for pn in parameternames:
                                    try:

                                        # print "finding parameter " +
                                        #     pn.name + " in metadata"

                                        dfile = Dataset_File.objects.get(
                                            pk=current_df_id)
                                        if pn.data_type == ParameterName.NUMERIC:
                                            value = \
                                getParameterFromTechXML(tech_xml, pn.name)

                                            if value != None:
                                                dp = DatafileParameter(
                                                parameterset=parameterset,
                                                    name=pn,
                                                    string_value=None,
                                            numerical_value=float(value))

                                                dp.save()
                                        else:
                                            dp = \
    DatafileParameter(parameterset=parameterset, name=pn,
              string_value=getParameterFromTechXML(tech_xml,
              pn.name), numerical_value=None)
                                            dp.save()
                                    except e:
                                        logger.debug('error saving ' +
                                            'experiment parameter: ' + e)
                            except Schema.DoesNotExist, e:
                                logger.debug('schema not found: ' + e)

            try:
                # logger.debug('attempting to parse line: ' + line)
                dom = parseString(line)
                doc = dom.documentElement

                tag_name = doc.tagName
                logger.debug(tag_name + ' discovered')
                if current == 'experiment':
                    if tag_name in ['title', 'organization',
                                    'starttime', 'endtime']:
                        contents = doc.childNodes
                        exp[tag_name] = getText(contents)
                    if tag_name == 'author':
                        contents = doc.childNodes
                        authors.append(getText(contents))
                if current == 'dataset':
                    if tag_name == 'description':
                        contents = doc.childNodes
                        dataset[tag_name] = getText(contents)
                if current == 'file':
                    if tag_name == 'name' or tag_name == 'size' or \
                            tag_name == 'path':
                        contents = doc.childNodes
                        datafile[tag_name] = getText(contents)
            except:
                pass

        return experiment.id
