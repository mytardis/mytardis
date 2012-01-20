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
spctags.py

.. moduleauthor:: Joanna H. Huang <Joanna.Huang@versi.edu.au>

"""

from tardis.tardis_portal.models import Schema, DatafileParameterSet
from tardis.tardis_portal.models import ParameterName, DatafileParameter
import logging
import struct
import string

from django.conf import settings


logger = logging.getLogger(__name__)

class SPCTagsFilter(object):
    """This filter provides extraction of metadata extraction of 
    EDAX Genesis spectral files (*.spc) from the RMMF.

    If a white list is specified then it takes precedence and all
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
        
        # NULL-terminated string, the byte value is HEX 0
        self.terminator = '\x00'
        # binary computing format and size.
        # example: binary_format = {"format": ("type", size)}
        self.binary_format = {"c": ("char",   1),
                              "f": ("float",  4),
                              "d": ("double", 8),
                              "h": ("short",  2),
                              "l": ("long",   4),
                              }
        # shown spectral fields
        # example: fields = {offset: ("field name", 
        #                             "binary format", 
        #                             integer (rounded to n digits after the decimal point), 
        #                             "unit")}
        self.fields = {104: ("Sample Type (Label)",        "c", None, None),
                       392: ("Preset",                     "f",    1, None),
                       456: ("Live Time",                  "f",    1, "sec"),
                       532: ("Acc. Voltage",               "f",    3, "kV"),
                       638: ("Number of Peak ID Elements", "h",    0, None),
                       }
        
        # Atomic elements from http://en.wikipedia.org/wiki/List_of_elements
        # example: atomic_elements = {atomic_number: "atomic_symbol"}
        self.atomic_elements = {
              1:   "H",   2:  "He",   3:  "Li",   4:  "Be",   5:   "B",   6:   "C",   7:   "N",   8:   "O",   9:   "F",  10:  "Ne",
             11:  "Na",  12:  "Mg",  13:  "Al",  14:  "Si",  15:   "P",  16:   "S",  17:  "Cl",  18:  "Ar",  19:   "K",  20:  "Ca",
             21:  "Sc",  22:  "Ti",  23:   "V",  24:  "Cr",  25:  "Mn",  26:  "Fe",  27:  "Co",  28:  "Ni",  29:  "Cu",  30:  "Zn",
             31:  "Ga",  32:  "Ge",  33:  "As",  34:  "Se",  35:  "Br",  36:  "Kr",  37:  "Rb",  38:  "Sr",  39:   "Y",  40:  "Zr",
             41:  "Nb",  42:  "Mo",  43:  "Tc",  44:  "Ru",  45:  "Rh",  46:  "Pd",  47:  "Ag",  48:  "Cd",  49:  "In",  50:  "Sn",
             51:  "Sb",  52:  "Te",  53:   "I",  54:  "Xe",  55:  "Cs",  56:  "Ba",  57:  "La",  58:  "Ce",  59:  "Pr",  60:  "Nd",
             61:  "Pm",  62:  "Sm",  63:  "Eu",  64:  "Gd",  65:  "Tb",  66:  "Dy",  67:  "Ho",  68:  "Er",  69:  "Tm",  70:  "Yb",
             71:  "Lu",  72:  "Hf",  73:  "Ta",  74:   "W",  75:  "Re",  76:  "Os",  77:  "Ir",  78:  "Pt",  79:  "Au",  80:  "Hg",
             81:  "Tl",  82:  "Pb",  83:  "Bi",  84:  "Po",  85:  "At",  86:  "Rn",  87:  "Fr",  88:  "Ra",  89:  "Ac",  90:  "Th",
             91:  "Pa",  92:   "U",  93:  "Np",  94:  "Pu",  95:  "Am",  96:  "Cm",  97:  "Bk",  98:  "Cf",  99:  "Es", 100:  "Fm",
            101:  "Md", 102:  "No", 103:  "Lr", 104:  "Rf", 105:  "Db", 106:  "Sg", 107:  "Bh", 108:  "Hs", 109:  "Mt", 110:  "Ds",
            111:  "Rg", 112:  "Cn", 113: "Uut", 114: "Uuq", 115: "Uup", 116: "Uuh", 117: "Uus", 118: "Uuo", 
        }
        
        # Shells
        self.shells = {1: "K", 6: "L", 16: "M"}
        
        self.instruments = {'Quanta200': (('EDAXGenesis_SPC', 'EDAXGenesis_SPC', None),),
                            'NovaNanoSEM': (('EDAXGenesis_SPC', 'EDAXGenesis_SPC', None),),
                            }
        
        logger.debug('initialising SPCTagsFilter')

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
        
        #ignore non-spectra file
        if filepath[-4:].lower() != ".spc":
            return
        
        # Find instrument name in filepath
        instr_name = None 
        import re
        pathSep = re.compile(r'\\|\/')
        for part in pathSep.split(filepath):
            if part in self.instruments.keys():
                instr_name = part

        logger.debug("filepath=%s" % filepath)
        logger.debug("instr_name=%s" % instr_name)

        if (instr_name != None and len(instr_name) > 1):
            
            # get spectral metadata 
            metadata = self.getSpectra(filepath)
        
            # get schema (create schema if needed)
            instrSchemas = self.instruments[instr_name]
            schema_name = "EDAXGenesis_SPC"
            for sch in instrSchemas:
                if sch[0] == schema_name:
                    (schemaName, schemaSuffix, tagsToFind) = sch
            if not schemaName:
                logger.debug("Schema %s doesn't exist for instrument %s" % (schema_name, instr_name))
                return
            instrNamespace = ''.join([self.schema, "/" , schemaSuffix]) 
            (schema, created) = Schema.objects.get_or_create(namespace=instrNamespace, name=schemaName,type=Schema.DATAFILE)
            if created: # new object was created
                schema.save()
                
            # save spectral metadata
            self.saveSpectraMetadata(instance, schema, metadata)

    def saveSpectraMetadata(self, instance, schema, metadata):
        """Save all the metadata to a Dataset_Files paramamter set.
        """
        parameters = self.getParamaters(schema, metadata)
        if not parameters:
            return None
        
        (ps, created) = DatafileParameterSet.objects.get_or_create(schema=schema, dataset_file=instance)
        if created: # new object was created
            ps.save()
        else: # if parameter set already exists then just return it
            return ps 

        # save datafile parameters
        for p in parameters:
            if p.name in metadata:
                dfp = DatafileParameter(parameterset=ps,
                                        name=p)
                if p.isNumeric():
                    dfp.numerical_value = metadata[p.name][0]
                else:
                    dfp.string_value = metadata[p.name][0]
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
             
            # integer data type test
            try:
                int(metadata[p][0])
            except (ValueError, TypeError):
                pass
            else:
                datatype = ParameterName.NUMERIC
            
            # float data type test
            try:
                float(metadata[p][0])
            except (ValueError, TypeError):
                pass
            else:
                datatype = ParameterName.NUMERIC

            unit = ""
            if metadata[p][1]:
                unit = metadata[p][1]
      
            new_param = ParameterName(schema=schema,
                                      name=p,
                                      full_name=p,
                                      data_type=datatype,
                                      units=unit)
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




    def getSpectra(self, filename):
        """Return a dictionary of the metadata.
        """
        logger.debug("Extracting spectral metadata from *.spc file...")
        ret = {}
        try:
            spc = open(filename)
            offsets = self.fields.keys()
            offsets.sort()
            for offset in offsets:
                
                # get field
                field = self.fields[offset][0]
                
                # get value
                spc.seek(offset)
                field_name = self.fields[offset][0]
                format = self.fields[offset][1]
                rounded_digits = self.fields[offset][2]
                unit = self.fields[offset][3]
                byte_size = self.binary_format[format][1]
                if format == 'c': # extract strings
                    value_string = spc.next()
                    string_length = value_string.find('\x00')
                    value = ""
                    if string_length > 0:
                        spc.seek(offset)
                        value_tuple = struct.unpack(format * string_length, spc.read(byte_size * string_length))
                        value = string.join(value_tuple,"")
                elif field_name == "Number of Peak ID Elements": # extract atomic peak numbers
                    number_of_peak = struct.unpack(format, spc.read(byte_size))[0]
                    atomic_offset = offset + 2 # should be 640 for the beginning offset of atomic numbers
                    line_offset = 736 # the beginning offset of line numbers
                    energy_offset = 832 # the beginning offset of energy numbers
                    height_offset = 1024 # the beginning offset of height numbers
                    energy_step = 0
                    height_step = 0
                    for peak_offset in range(atomic_offset, atomic_offset+number_of_peak*2, 2):
                        # Atomic
                        spc.seek(peak_offset)
                        atomic_value = struct.unpack(format, spc.read(byte_size))[0]
                        
                        # Line
                        spc.seek(line_offset+peak_offset-atomic_offset)
                        line_value = struct.unpack(format, spc.read(byte_size))[0]
                        if line_value < 6: # K shells: 1-5
                            line_value = 1
                        elif line_value >= 6 and line_value <16: # L shells: 6-15
                            line_value = 6
                        else: # M shells: 16~
                            line_value = 16
                        
                        # Energy
                        spc.seek(energy_offset + energy_step)
                        energy_value = struct.unpack('f', spc.read(4))[0]
                        energy_step += 4
                        
                        # Height
                        print "offset ", height_offset + height_step
                        spc.seek(height_offset + height_step)
                        height_value = struct.unpack('I', spc.read(4))[0]
                        print "height_value ", height_value
                        height_step += 4
                        
                        # compose the peak value
                        value = "Atomic=%s, Line=%s, Energy=%.4f, Height=%d" % \
                                (self.atomic_elements[int(atomic_value)], 
                                 self.shells[line_value], 
                                 energy_value, 
                                 height_value)
                        ret["Peak ID Element %s" % ((peak_offset-atomic_offset)/2+1)] = [value, unit]
                    continue
                else: # extract numbers
                    value = round( struct.unpack(format, spc.read(byte_size))[0], rounded_digits)
                
                ret[field] = [value, unit]
        except:
            print "Failed to extract spectral metadata from *.spc file."
            import sys
            #print sys.exc_info()
            #print ret
            logger.debug("Failed to extract spectral metadata from *.spc file.")
            return ret
        
        logger.debug("Successed extracting spectral metadata from *.spc file.")
        return ret

def make_filter(name='', schema='', tagsToFind=[], tagsToExclude=[]):
    if not name:
        raise ValueError("SPCTagsFilter requires a name to be specified")
    if not schema:
        raise ValueError("SPCTagsFilter required a schema to be specified") 
    return SPCTagsFilter(name, schema, tagsToFind, tagsToExclude)

make_filter.__doc__ = SPCTagsFilter.__doc__