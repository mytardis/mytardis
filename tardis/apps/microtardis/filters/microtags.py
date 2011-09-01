# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2011, RMIT e-Research Office
#   (RMIT University, Australia)
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
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

"""
microtags.py

.. moduleauthor:: Russell Sim <russell.sim@monash.edu>
.. moduleauthor:: Ian Thomas <Ian.Edward.Thomas@rmit.edu.au>

"""
from fractions import Fraction

try:
    from pyexiv2 import Image
    from pyexiv2 import Rational
except:
    raise ImportError("Can't import pyexiv2 please install it")

from tardis.tardis_portal.models import Schema, DatafileParameterSet
from tardis.tardis_portal.models import ParameterName, DatafileParameter
import logging


logger = logging.getLogger(__name__)

class MicroTagsFilter(object):
    """This filter provides extraction of metadata extraction of images from the RMMF
    from images.

    If a white list is specified then it takes precidence and all
    other tags will be ignored.

    :param name: the short name of the schema.
    :type name: string
    :param schema: the name of the schema to load the EXIF data into.
    :type schema: string
    :param tagsToFind: a list of the tags to include.
    :type tagsToFind: list of strings
    :param tagsToExclude: a list of the tags to exclude.
    :type tagsToExclude: list of strings
    """
    def __init__(self, name, schema, tagsToFind=[], tagsToExclude=[]):
        self.name = name
        self.schema = schema
        self.tagsToFind = tagsToFind
        self.tagsToExclude = tagsToExclude

        self.delim = '\r\n'
        self.instruments = {'FEIQuanta200':(('FEIQuanta-1','FEIQuanta1',('HV','Spot','abc')),('FEIQuanta-2','FEIQuanta2',('Brightness',))),
 			    'nanoSEM':(('nanoSEM','nanoSEM',('HV','PixelHeight','Aperture')),)}
        logger.debug('initialising MicroTagsFilter')

    def __call__(self, sender, **kwargs):
        """post save callback entry point.

        :param sender: The model class.
        :param instance: The actual instance being saved.
        :param created: A boolean; True if a new record was created.
        :type created: bool
        """
        instance = kwargs.get('instance')
        created = kwargs.get('created')
        if not created:
            # Don't extract on edit
            return
        #  schema = self.getSchema()
        
        
        filepath = instance.get_absolute_filepath()
        if not filepath:
            # TODO log that exited early
            return
        
       
        # Find instrument name in filepath
        filterMatch = None 
        import re
        pathSep = re.compile(r'\\|\/')
        for part in pathSep.split(filepath):
            if part in self.instruments.keys():
                filterMatch = part

        logger.debug("filepath=%s" % filepath)
        logger.debug("filterMatch=%s" % filterMatch)

        if (filterMatch != None and len(filterMatch) > 1):
            
            logger.debug("filterMatch %s" % filterMatch)
            exifs = self.getExif(filepath)

            for exifTag in exifs:
                logger.debug("exifTag=%s" % exifTag)
                if exifTag == 'Exif.Image.0x877a':
                    
                    # splitup tag value
                    splited =  exifs[exifTag].split(self.delim)                  
                    nosections = [ e for e in splited if (len(e) > 0 
                              and e[0] != '[' and e[-1] != ']')]
                    instrSchemas = self.instruments[filterMatch]

                    # for each schema for this instrument 
                    for sch in instrSchemas:
                     
                        (schemaName,schemaSuffix,tagsToFind) = sch
                        logger.debug("schemaTuple %s  = %s %s %s" %(sch,schemaName,schemaSuffix,tagsToFind))

                        # find property value in tag
                        metadata = {}
                        for keyval in nosections:
                            (key,val) = keyval.split('=')
                            if key in tagsToFind:
                                metadata[key]=val

                        # only save exif data if we found some expected metadata
                        logger.debug("metadata = %s" % metadata)
                        if len(metadata) > 0:
                            # Make instrument specific schema                          
                            logger.debug("existing schema is %s" % self.schema)
                            instrNamespace = ''.join([self.schema, "/" , schemaSuffix]) 

                            logger.debug("full instrument schema namespace is %s" %instrNamespace)
                            logger.debug("full instrument schema name is %s" %schemaName)

                            # create schema if needed
                            try:
                                schema =  Schema.objects.get(namespace__exact=instrNamespace)
                                logger.debug("found existing metadata schema %s" % schema)
                            except Schema.DoesNotExist:
                                schema = Schema(namespace=instrNamespace, name=schemaName,type=Schema.DATAFILE)
                                logger.debug("creating new metadata schema %s" % schema)
                                schema.save()
                            # and save metadata
                            ps = self.saveExifMetadata(instance, schema, metadata)
                            logger.debug("ps=%s" % ps)

    def saveExifMetadata(self, instance, schema, metadata):
        """Save all the metadata to a Dataset_Files paramamter set.
        """
        parameters = self.getParamaters(schema, metadata)
        if not parameters:
            return None

        try:
            ps = DatafileParameterSet.objects.get(schema=schema,
                                                  dataset_file=instance)
            return ps  # if already exists then just return it
        except DatafileParameterSet.DoesNotExist:
            ps = DatafileParameterSet(schema=schema,
                                      dataset_file=instance)
            ps.save()

        for p in parameters:
            if p.name in metadata:
                dfp = DatafileParameter(parameterset=ps,
                                        name=p)
                if p.isNumeric():
                    dfp.numerical_value = metadata[p.name]
                else:
                    dfp.string_value = metadata[p.name]
                dfp.save()
        return ps

    def getParamaters(self, schema, metadata):
        """Return a list of the paramaters that will be saved.
        """
        param_objects = ParameterName.objects.filter(schema=schema)
        parameters = []
        for p in metadata:

            if self.tagsToFind and not p in self.tagsToFind:
                continue

            if p in self.tagsToExclude:
                continue

            parameter = filter(lambda x: x.name == p, param_objects)

            if parameter:
                parameters.append(parameter[0])
                continue

            # detect type of parameter
            datatype = ParameterName.STRING
             
            if isinstance(metadata[p], Rational):
                datatype = ParameterName.STRING
            # Fraction test
            elif isinstance(metadata[p], Fraction):
                datatype = ParameterName.STRING
            else:
                # Int test
                try:
                    int(metadata[p])
                except ValueError:
                    pass
                except TypeError:
                    pass
                else:
                    datatype = ParameterName.NUMERIC
    
                # Float test
                try:
                    float(metadata[p])
                except ValueError:
                    pass
                except TypeError:
                    pass
                else:
                    datatype = ParameterName.NUMERIC

            new_param = ParameterName(schema=schema,
                                      name=p,
                                      full_name=p,
                                      data_type=datatype)
            new_param.save()
            parameters.append(new_param)
        return parameters

    def getSchema(self):
        """Return the schema object that the paramaterset will use.
        """
        try:
            return Schema.objects.get(namespace__exact=self.schema)
        except Schema.DoesNotExist:
            schema = Schema(namespace=self.schema, name=self.name,
                            type=Schema.DATAFILE)
            schema.save()
            return schema

    def getExif(self, filename):
        """Return a dictionary of the metadata.
        """

        ret = {}
        image = Image(filename)
        try:
            image.readMetadata()
        except IOError:
            return ret
        for tag in image.exifKeys():
            ret[tag] = image[tag]
        return ret



def make_filter(name='', schema='', tagsToFind=[], tagsToExclude=[]):
    if not name:
        raise ValueError("MicroTagsFilter requires a name to be specified")
    if not schema:
        raise ValueError("MictoTagsFilter required a schema to be specified") 
    return MicroTagsFilter(name, schema, tagsToFind, tagsToExclude)

make_filter.__doc__ = MicroTagsFilter.__doc__
