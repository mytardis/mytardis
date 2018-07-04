# -*- coding: utf-8 -*-
#
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
diffractionimage.py

.. moduleauthor:: Steve Androulakis <steve.androulakis@gmail.com>

"""
import base64
from fractions import Fraction
import logging
import subprocess
import tempfile
import warnings

from tardis.tardis_portal.deprecations import RemovedInMyTardis40Warning
from tardis.tardis_portal.models import Schema, DatafileParameterSet
from tardis.tardis_portal.models import ParameterName, DatafileParameter

logger = logging.getLogger(__name__)


class DiffractionImageFilter(object):
    """This filter runs the CCP4 diffdump binary on a diffraction image
    and collects its output into the trddatafile schema

    If a white list is specified then it takes precidence and all
    other tags will be ignored.

    param name: the short name of the schema.
    type name: string
    param schema: the name of the schema to load the EXIF data into.
    type schema: string
    param tagsToFind: a list of the tags to include.
    type tagsToFind: list of strings
    param tagsToExclude: a list of the tags to exclude.
    type tagsToExclude: list of strings
    """
    def __init__(self, name, schema, diffdump_path, diff2jpeg_path,
                 tagsToFind=[], tagsToExclude=[]):
        self.name = name
        self.schema = schema
        self.tagsToFind = tagsToFind
        self.tagsToExclude = tagsToExclude
        self.diffdump_path = diffdump_path
        self.diff2jpeg_path = diff2jpeg_path

        # these values map across directly
        self.terms = {
            'Imagetype': "imageType",
            'Collectiondate': "collectionDate",
            'Exposuretime': "exposureTime",
            'DetectorS/N': "detectorSN",
            'Wavelength': "wavelength",
            'Distancetodetector': "detectorDistance",
            'TwoThetavalue': "twoTheta",
        }

        self.values = {
            'Imagetype': self.output_metadata,
            'Collectiondate': self.output_metadata,
            'Exposuretime': self.output_exposuretime,
            'DetectorS/N': self.output_metadata,
            'Wavelength': self.output_wavelength,
            'Beamcenter': self.output_beamcenter,
            'Distancetodetector': self.output_detectordistance,
            'ImageSize': self.output_imagesize,
            'PixelSize': self.output_pixelsize,
            'Oscillation(phi)': self.output_oscillation,
            'TwoThetavalue': self.output_twotheta,
        }

    def __call__(self, sender, **kwargs):
        """post save callback entry point.

        param sender: The model class.
        param instance: The actual instance being saved.
        param created: A boolean; True if a new record was created.
        type created: bool
        """
        warnings.warn(
            "The diffractionimage filter will be removed in MyTardis 4.0. "
            "It is no longer used in the MyTardis deployment it was developed "
            "for, and it is too deployment-specific to be included in the "
            "core MyTardis repository.",
            RemovedInMyTardis40Warning
        )
        instance = kwargs.get('instance')

        schema = self.getSchema()

        filepath = instance.get_absolute_filepath()

        try:
            metadata = self.getDiffractionImageMetadata(filepath)

            previewImage64 = self.getDiffractionPreviewImage(filepath)

            if previewImage64:
                metadata['previewImage'] = previewImage64

            self.saveDiffractionImageMetadata(instance, schema, metadata)
        except Exception, e:
            logger.debug(e)

    def saveDiffractionImageMetadata(self, instance, schema, metadata):
        """Save all the metadata to a DataFiles paramamter set.
        """
        parameters = self.getParameters(schema, metadata)
        if not parameters:
            return None

        try:
            ps = DatafileParameterSet.objects.get(schema=schema,
                                                  datafile=instance)
            return ps  # if already exists then just return it
        except DatafileParameterSet.DoesNotExist:
            ps = DatafileParameterSet(schema=schema,
                                      datafile=instance)
            ps.save()

        for p in parameters:
            if p.name in metadata:
                dfp = DatafileParameter(parameterset=ps,
                                        name=p)
                if p.isNumeric():
                    if metadata[p.name] != '':
                        dfp.numerical_value = metadata[p.name]
                        dfp.save()
                else:
                    dfp.string_value = metadata[p.name]
                    dfp.save()

        return ps

    def getParameters(self, schema, metadata):
        """Return a list of the paramaters that will be saved.
        """
        param_objects = ParameterName.objects.filter(schema=schema)
        parameters = []
        for p in metadata:

            if self.tagsToFind and p not in self.tagsToFind:
                continue

            if p in self.tagsToExclude:
                continue

            parameter = filter(lambda x, _p=p: x.name == _p, param_objects)

            if parameter:
                parameters.append(parameter[0])
                continue

            # detect type of parameter
            # datatype = ParameterName.STRING

            # Int test
            try:
                int(metadata[p])
            except ValueError:
                pass
            except TypeError:
                pass
            else:
                pass
                # datatype = ParameterName.NUMERIC

            # Fraction test
            if isinstance(metadata[p], Fraction):
                pass
                # datatype = ParameterName.NUMERIC

            # Float test
            try:
                float(metadata[p])
            except ValueError:
                pass
            except TypeError:
                pass
            else:
                pass
                # datatype = ParameterName.NUMERIC
            # the datatype test is not actually being used, it seems.
            # TODO revise this function for usefulness
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

    def getDiffractionImageMetadata(self, filename):
        """Return a dictionary of the metadata.
        """
        ret = {}

        try:
            output = self.run_diffdump(filename)

            tags = self.parse_output(output)
        except IOError:
            return ret

        for tag in tags:
            ret[tag['key']] = tag['value']
        return ret

    def getDiffractionPreviewImage(self, filename):
        """Return a base64 encoded preview image.
        """
        try:
            previewImage64 = self.run_diff2jpeg(filename)

            return previewImage64

        except IOError:
            return None

    def parse_term(self, line):
        return line.split(':')[0].replace(' ', '')

    def parse_value(self, line):
        return line.split(':')[1].replace('\n', '').strip()

    def output_metadata(self, term, value):
        return {'key': self.terms[term], 'value': value}

    def output_exposuretime(self, term, value):
        return self.output_metadata(term, value.replace('s', ''))

    def output_wavelength(self, term, value):
        return self.output_metadata(term, value.replace('Ang', ''))

    def output_detectordistance(self, term, value):
        return self.output_metadata(term, value.replace('mm', ''))

    def output_twotheta(self, term, value):
        return self.output_metadata(term, value.replace('deg', ''))

    def split_output(self, terms, value, strip):
        values = value.split(',')
        split = []
        split.append({'key': terms[0],
                      'value': values[0][1:].replace(strip, '')})
        split.append({'key': terms[1],
                      'value': values[1][:-1].replace(strip, '')})
        return split

    def split_oscillation(self, terms, value):
        values = value.split('->')
        split = []
        split.append({'key': terms[0],
                      'value': values[0]})
        split.append({'key': terms[1],
                      'value': values[1][:-3]})
        return split

    def output_beamcenter(self, term, value):
        return self.split_output(['directBeamXPos', 'directBeamYPos'],
                                 value, 'mm')

    def output_imagesize(self, term, value):
        return self.split_output(['imageSizeX', 'imageSizeY'],
                                 value, 'px')

    def output_pixelsize(self, term, value):
        return self.split_output(['pixelSizeX', 'pixelSizeY'],
                                 value, 'mm')

    def output_oscillation(self, term, value):
        return self.split_oscillation(
            ['oscillationRangeStart', 'oscillationRangeEnd'], value)

    def parse_output(self, output):
        metadata = []
        for line in output:
            term = self.parse_term(line)
            value = self.parse_value(line)

            try:
                value_outputs = self.values[term](term, value)

                if isinstance(value_outputs, list):

                    for value_output in value_outputs:

                        metadata.append(value_output)
                else:
                    metadata.append(value_outputs)

            except KeyError:
                logger.debug('no ' + str(term) + ' found')

        return metadata

    def run_diffdump(self, file_path):
        split_diffdump_path = self.diffdump_path.rsplit('/', 1)
        cd = split_diffdump_path[0]
        diffdump_exec = split_diffdump_path[1]

        cmd = "cd '" + cd + "'; ./'" + diffdump_exec + "' '" + file_path + "'"
        with open("test2.txt", "a") as myfile:
            myfile.write(cmd)
        output = subprocess.Popen(cmd,
                                  stdout=subprocess.PIPE,
                                  shell=True).stdout

        return output

    def run_diff2jpeg(self, filename):
        split_diff2jpeg_path = self.diff2jpeg_path.rsplit('/', 1)
        cd = split_diff2jpeg_path[0]
        diff2jpeg_exec = split_diff2jpeg_path[1]

        tf = tempfile.NamedTemporaryFile()

        cmd = "cd '" + cd + "'; ./'" + diff2jpeg_exec + "' '" + filename +\
              "' '" + tf.name + "'"

        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             shell=True)

        p.wait()

        result_str = p.stdout.read()

        encoded = None
        if not result_str.startswith('Exception'):
            read = tf.read()
            encoded = base64.b64encode(read)

        tf.close()
        return encoded


def make_filter(name='', schema='', tagsToFind=[], tagsToExclude=[]):
    if not name:
        raise ValueError("DiffractionImageFilter "
                         "requires a name to be specified")
    if not schema:
        raise ValueError("DiffractionImageFilter "
                         "requires a schema to be specified")
    return DiffractionImageFilter(name, schema, tagsToFind, tagsToExclude)
make_filter.__doc__ = DiffractionImageFilter.__doc__
