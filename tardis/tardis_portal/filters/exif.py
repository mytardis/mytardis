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
exif.py

.. moduleauthor:: Russell Sim <russell.sim@monash.edu>

"""
from fractions import Fraction

try:
    from pyexiv2 import ImageMetadata
except:
    ImportError("Can't import pyexiv2 please install it")

from tardis.tardis_portal.models import Schema, DatafileParameterSet
from tardis.tardis_portal.models import ParameterName, DatafileParameter


class EXIFFilter(object):
    def __init__(self, schema, tagsToFind=None, tagsToExclude=None):
        self.schema = schema
        self.tagsToFind = tagsToFind
        self.tagsToExclude = tagsToExclude

    def __call__(self, sender, **kwargs):
        """
        post save callback

        sender
            The model class.
        instance
            The actual instance being saved.
        created
            A boolean; True if a new record was created.
        """
        instance = kwargs.get('instance')
        created = kwargs.get('created')
        if not created:
            # Don't extract on edit
            return
        schema = self.getSchema()
        filepath = instance.get_absolute_filepath()
        if not filepath:
            # TODO log that exited early
            return
        metadata = self.getExif(filepath)
        self.saveExifMetadata(instance, schema, metadata)

    def saveExifMetadata(self, instance, schema, metadata):
        try:
            ps = DatafileParameterSet.objects.get(schema=schema,
                                                  dataset_file=instance)
            return ps  # if already exists then just return it
        except DatafileParameterSet.DoesNotExist:
            ps = DatafileParameterSet(schema=schema,
                                      dataset_file=instance)
            ps.save()
        parameters = self.getParamaters(schema, metadata)
        for p in parameters:
            if p.name in metadata:
                dfp = DatafileParameter(parameterset=ps,
                                        name=p)
                if p.is_numeric:
                    dfp.numerical_value = metadata[p.name]
                else:
                    dfp.string_value = metadata[p.name]
                dfp.save()
        return ps

    def getParamaters(self, schema, metadata):
        param_objects = ParameterName.objects.filter(schema=schema)
        parameters = []
        for p in metadata:
            # TODO need to check if the paramter exists
            # or if it should be skipped
            if False:
                raise Exception()

            # detect type of parameter
            is_numeric = False

            # Int test
            try:
                int(metadata[p])
            except ValueError:
                pass
            except TypeError:
                pass
            else:
                is_numeric = True

            # Fraction test
            if isinstance(metadata[p], Fraction):
                is_numeric = True

            # Float test
            try:
                float(metadata[p])
            except ValueError:
                pass
            except TypeError:
                pass
            else:
                is_numeric = True

            new_param = ParameterName(schema=schema,
                                      name=p,
                                      full_name=p,
                                      is_numeric=is_numeric)
            new_param.save()
            parameters.append(new_param)
        return parameters

    def getSchema(self):
        try:
            return Schema.objects.get(namespace__exact=self.schema)
        except Schema.DoesNotExist:
            schema = Schema(namespace=self.schema)
            schema.save()
            return schema

    def getExif(self, filename):
        ret = {}
        image = ImageMetadata(filename)
        image.read()
        for tag in image.values():
            ret[tag.key] = tag.value
        return ret
