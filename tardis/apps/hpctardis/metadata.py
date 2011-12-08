# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2011, RMIT e-Research Office
#   (RMIT University, Australia)
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
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
metadata.py

.. moduleauthor:: Ian Thomas <Ian.Edward.Thomas@rmit.edu.au>

"""
from os import path
import re
import itertools
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from tardis.tardis_portal.models import Dataset_File
from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.models import DatafileParameter
from tardis.tardis_portal.models import DatafileParameterSet
from tardis.tardis_portal.models import ParameterName
from tardis.tardis_portal.models import Schema
from tardis.tardis_portal.models import DatasetParameter
from tardis.tardis_portal.models import DatasetParameterSet
from tardis.tardis_portal.models import Experiment


logger = logging.getLogger(__name__)

number = "[+-]?((\d+)(\.\d*)?)|(\d+\.\d+)([eE][+-]?[0-9]+)?"
rulesets = {
            ('http://tardis.edu.au/schemas/general/1','general 1.0'):
            ( ('Project',("^.*[_0-9]*\.o(\d+)$",),
                 "get_file_regex(context,'Project:\s+(?P<value>[^\s]+)\s(?P<unit>)',True)"), 
              ('Number Of CPUs',("^.*[_0-9]*\.o(\d+)$",),
                 "get_file_regex(context,'Number of cpus:\s+(?P<value>.+)(?P<unit>)',True)"),
                ('Maximum virtual memory',("^.*[_0-9]*\.o(\d+)$",),
                 "get_file_regex(context,'Max virtual memory:\s+(?P<value>[0-9]+)(?P<unit>(M|G|K)B)',True)"),
                ('Max jobfs disk use',("^.*[_0-9]*\.o(\d+)$",),
                 "get_file_regex(context,'Max jobfs disk use:\s+(?P<value>.*)(?P<unit>(M|G|K)B)',True)"),
                ('Walltime',("^.*[_0-9]*\.o(\d+)$",),
                 "get_file_regex(context,'Elapsed time:\s+(?P<value>[\w:]+)(?P<unit>)',True)")),
            
            ('http://tardis.edu.au/schemas/vasp/1','vasp 1.0'):
            (
                ('kpoint_grid',("KPOINTS[_0-9]*",),
                 "get_file_line(context,-3)"),
                ('kpoint_grid_offset',("KPOINTS[_0-9]*",),
                 "get_file_line(context,-2)"),
                 # TODO: remove number as can cause bad matches 
                ('ENCUT',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'\s+ENCUT\s*=\s*(?P<value>%s)\s+(?P<unit>eV)',False)" % number),
                ('NIONS',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'\s+NIONS\s*\=\s*(?P<value>%s)(?P<unit>)',False)" % number), 
                ('NELECT',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'\s+NELECT\s*\=\s*(?P<value>%s)\s+(?P<unit>.*)$',False)" % number),
                ('ISIF',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'\s+ISIF\s+\=\s+(?P<value>%s)\s+(?P<unit>.*)$',False)" % number),  
                ('ISPIN',("OUTCAR[0-9]*",),
                 "get_file_regex(context,'\s+ISPIN\s+\=\s+(?P<value>%s)\s+(?P<unit>.*)$',False)" % number),                  
               
                
                ('NSW',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'NSW\s*\=\s*(?P<value>%s)\s*(?P<unit>.*)$',False)" % number),
                ('IBRION',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'IBRION\s*\=\s*(?P<value>%s)\s+(?P<unit>.*)$',False)" % number),
                ('ISMEAR',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'ISMEAR\s*\=\s*(?P<value>%s)(?P<unit>)',False)" % number),
                ('POTIM',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'POTIM\s*\=\s*(?P<value>%s)(?P<unit>)',False)" % number),
                #('MAGMOM',("POSCAR[_0-9]*",),
                 #"get_file_lines(context,1,4)"), 
                ('Descriptor Line',("INCAR[_0-9]*",),
                 "get_file_regex(context,'System = (?P<value>.*)(?P<unit>)',False)"), 
                ('EDIFF',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'EDIFF\s*\=\s*(?P<value>[^\s]+)(?P<unit>)',False)"), 
                ('EDIFFG',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'EDIFFG\s*\=\s*(?P<value>[^\s]+)(?P<unit>)',False)"), 
                ('NELM',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'NELM\s*\=\s*(?P<value>[^;\s]+)(?P<unit>)',False)"), 
                ('ISTART',("INCAR[_0-9]*",),
                 "get_file_regex(context,'ISTART\s*\=\s*(?P<value>[^;\s]+)(?P<unit>)',False)"), 
                ('TEBEG',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'TEBEG\s*\=\s*(?P<value>[^;\s]+)(?P<unit>)',False)"), 
                ('TEEND',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'TEEND\s*\=\s*(?P<value>[^;\s]+)(?P<unit>.*)',False)"), 
                ('SMASS',("OUTCAR[_0-9]*",),
                 "get_file_regex(context,'SMASS\s*\=\s*(?P<value>[^\s]+)(?P<unit>.*)',False)"),  
                ('Final Iteration',("OSZICAR[_0-9]*",),
                 "get_final_iteration(context)"), 
             
                ('TITEL',("OUTCAR[_0-9]*",),
                 "('\\n '.join(get_file_regex_all(context,'TITEL\s+\=\s+(?P<value>.*)$')),'')"), 
             
                ('LEXCH',("OUTCAR[_0-9]*",),
                 "('\\n '.join(get_file_regex_all(context,'LEXCH\s+\=\s+(?P<value>[^\s]+)')),'')"), 
             
                ('Cell Scaling',("POSCAR[_0-9]*",),
                 "get_file_line(context,1)"),
            
                ('Cell Parameter1',("POSCAR[_0-9]*",),
                 "get_file_line(context,2)"),
            
                ('Cell Parameter2',("POSCAR[_0-9]*",),
                 "get_file_line(context,3)"),
            
                ('Cell Parameter3',("POSCAR[_0-9]*",),
                 "get_file_line(context,4)")),
            
            
            
                 
                 
                ('http://tardis.edu.au/schemas/siesta/1','siesta 1.0'):
                (('SystemName',("input[_0-9]*\.fdf",),
                   "get_file_regex(context,'SystemName\s+(?P<value>.*)(?P<unit>)',False)"),
                ('MeshCutoff',("input[_0-9]*\.fdf",),
                   "get_file_regex(context,'MeshCutoff\s+(?P<value>[^\s]+)(?P<unit>.*)',False)"),
                ('ElectronicTemperature',("input[_0-9]*\.fdf",),
                   "get_file_regex(context,'ElectronicTemperature\s+(?P<value>[^\s]+)(?P<unit>.*)',False)"),
                #('k-grid',("input\.fdf",),
                #   "get_regex_lines(context,'\%block k_grid_Monkhorst_Pack','\%endblock k_grid_Monkhorst_Pack')"),
                ('k-grid',("input[_0-9]*\.fdf",),
                   "get_regex_lines(context,'\%block kgridMonkhorstPack','\%endblock kgridMonkhorstPack')"),
                ('PAO.Basis',("input[_0-9]*\.fdf",),
                   "get_regex_lines(context,'\%block PAO.Basis','\%endblock PAO.Basis')"),
               
                ('MD.TypeOfRun',('input[_0-9]*\.fdf',),
                 "get_file_regex(context,'(?<!\#)MD\.TypeOfRun\s+(?P<value>.*)(?P<unit>)',False)"),
      
                ('MD.NumCGsteps',('input[_0-9]*\.fdf',),
                 "get_file_regex(context,'(?<!\#)MD\.NumCGsteps\s+(?P<value>[^\s]+)(?P<unit>)',False)"),
            
                ('iscf',('output[_0-9]*',),
                 "(get_regex_lines_vallist(context,'siesta\:\siscf','^$')[-1],'')"),
             
             
                ('E_KS',('output[_0-9]*',),
                 "get_file_regex(context,'^siesta:\s+E\_KS\(eV\)\s+\=\s+(?P<value>.*)(?P<unit>)',False)"),
             
                ('Occupation Function',('input[_0-9]*\.fdf',),
                 "get_file_regex(context,'(?<!\#)OccupationFunction\s+(?P<value>.*)(?P<unit>)',False)"),
             
                ('OccupationMPOrder',('input[_0-9]*\.fdf',),
                 "get_file_regex(context,'(?<!\#)OccupationMPOrder\s+(?P<value>.*)(?P<unit>)',False)"),
             
                
                ('MD.MaxForceTol',('input[_0-9]*\.fdf',),
                 "get_file_regex(context,'(?<!\#)MD\.MaxForceTol\s+(?P<value>[^\s]+)\s+(?P<unit>.*)',False)")),
                       
                       ('http://tardis.edu.au/schemas/test/1',''):(('Test',("R-2-2.tif",),
                  "get_constant(context,'99','foobars')"),
                 ('Test2',("R-2-2.tif","R-2-5.tif"),"get_constant(context,'hello','')"))
                 }

def _get_file_handle(context, filename):
    datafile = context['ready'][filename]
    url = datafile.get_download_url()
    file_handle = None
    if datafile.protocol == 'tardis' or datafile.url.startswith('tardis'):
        raw_path = url.partition('//')[2]
        file_path = path.join(settings.FILE_STORE_PATH,
                                  str(context['expid']),
                                  str(datafile.dataset.id),
                                  raw_path,datafile.url.partition('//')[2])
        
        logger.debug("file_path=%s" % file_path)
        
        file_handle = open(file_path,"r")
    return file_handle


def get_final_iteration(context):
    """ Return the final iteration number from a VASP run 
    """
    fileregex = context['fileregex'][0]
    filename = _get_file_from_regex(fileregex,context['ready'],False)
    logger.debug("filename=%s" % filename)
    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return ("","")
    else:
        logger.debug("found ready %s" % filename)
        try:
            fp = _get_file_handle(context, filename)
        except Exception:
            return ("","")
        if fp:
            regex = "RMM\:\s*(?P<value>\d+)\s*"
            regx = re.compile(regex)
            max_value = 0
            for line in fp:
                logger.debug("line=%s" % line)
                match = regx.search(line)  
                if match:
                    val = match.group('value') 
                    try:
                        value = int(val)
                    except ValueError:
                        value = 0
                    logger.debug("value=%s" % value)
                    if value > max_value:
                        max_value = value            
            fp.close()
            logger.debug("max_value = %s" % max_value)
            return (str(max_value),"") 
        else:
            return ("","")


def _get_file_from_regex(regex,context, return_max):
    """Returns the single key from ready dict which matches the regex.
    If return_max, then only use file which the largest group match in regex
    """
    regx = re.compile(regex)
    logger.debug("return_max=%s" % return_max)
    key = None
    max_match = ""
    max_value = 0
    logger.debug("regex=%s" % regex)
    for key in dict(context):
        logger.debug("key=%s" % key)
        match = regx.match(key)
        logger.debug("match=%s" % match)
        if return_max:
            logger.debug("return_max")
            if match:
                logger.debug("match=%s" % match)
                matched_groups = match.groups()
                if matched_groups:
                    if len(matched_groups) == 1:
                        if matched_groups[0] > max_value:
                            max_match = key
                            max_value=matched_groups[0]
        else:
            if match:
                logger.debug("matched to %s" % str(match.group(0)))
                return match.group(0) 
            
    logger.debug("max_match=%s" % max_match)
    return max_match



def get_file_lines(context, linestart,lineend):
    """ Returns value and units from the filenameregex where value is 
    newline joined lines from linestart to lineend.  Only works for local files""" 
    # match fileregex to available files
    #regx = re.compile(fileregex)
    #filename = None
    #for key in context['ready']:
    #    match = regx.match(key)
    #    if match:
    #        filename = key
    #        break
    fileregex = context['fileregex'][0]
    filename = _get_file_from_regex(fileregex,context['ready'],False)
    if filename not in context['ready']:
        return (None,'')
    else:
        
        try:
            fp = _get_file_handle(context, filename)
        except Exception:
            return ('','')
        if fp:
            res = []
            for i,line in enumerate(fp):
                if i in range(linestart,lineend):
                    res.append(line)
             
            return ("\n".join(res),'')
    return ('','')
    
    
    
def get_file_line(context,lineno):
    """Returns the context of relative linenumber
    Assumes no units value and only works for smallish file"""
    # match fileregex to available files
    #regx = re.compile(fileregex)
    #filename = None
    #for key in context['ready']:
        #match = regx.match(key)
        #if match:
            #filename = key
            #break
    fileregex = context['fileregex'][0]
  
    filename = _get_file_from_regex(fileregex,context['ready'],False)
    if filename not in context['ready']:
        return (None,'')
    else:
        try:
            fp = _get_file_handle(context, filename)
        except Exception:
            return ("","")
        if fp:
            line_list = fp.readlines()
            fp.close()
            logger.debug(line_list) 
            return (str(line_list[lineno]),'')
    return ('','')  
    

def get_regex_lines(context, startregex,endregex):
    
    fileregex = context['fileregex'][0]
  
    filename = _get_file_from_regex(fileregex,context['ready'],False)
    
    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return ('','')
    else:
        
        try:
            fp = _get_file_handle(context, filename)
        except Exception:
            return ('','')
        if fp:
            startreg = re.compile(startregex)
            endreg = re.compile(endregex)
            res = []
            in_region = False
            for line in fp:
                start_match = startreg.search(line)
                end_match = endreg.search(line)    
                if start_match:
                    in_region = True
                    continue
                if end_match:
                    in_region = False
                    continue
                if in_region:
                    res.append(line)
            fp.close() 
        return ("\n".join(res),'')     
                
                
                
                
def get_regex_lines_vallist(context, startregex,endregex):
    
    fileregex = context['fileregex'][0]
  
    filename = _get_file_from_regex(fileregex,context['ready'],False)
    
    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return ['']
    else:
        
        try:
            fp = _get_file_handle(context, filename)
        except Exception:
            return ['']
        if fp:
            startreg = re.compile(startregex)
            endreg = re.compile(endregex)
            res = []
            in_region = False
            for line in fp:
                start_match = startreg.search(line)
                end_match = endreg.search(line)    
                if start_match:
                    in_region = True
                    continue
                if end_match:
                    in_region = False
                    continue
                if in_region:
                    res.append(line)
            fp.close() 
        return res     
                
                
          
def get_file_regex(context,regex,return_max):
    """ Searches all files that match file regex and searches for regex in contents.
        Returns the contents of groups 'name' and 'unit' as a tuple
    """

    # match fileregex to available files
    #regx = re.compile(fileregex)
    #filename = None
    #for key in context['ready']:
    #    match = regx.match(key)
    #    if match:
    #        filename = key
    #        break

    # FIXME: only handles single file pattern    
    fileregex = context['fileregex'][0]
    filename = _get_file_from_regex(fileregex,context['ready'],return_max)
    
    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return ('','')
    else:
        try:
            fp = _get_file_handle(context, filename)
        except Exception,e:
            logger.error("problem with filehandle %s" % e)
            return ('','')
        if fp:
            regx = re.compile(regex)
            for line in fp:
                match = regx.search(line)
                
                if match:
                    value = match.group('value')
                    unit = str(match.group('unit'))
                    if not unit:
                        unit = ''
                    logger.debug("value=%s unit=%s" % (value,unit))
                    fp.close()
                    res = (value,unit)
                    for g in res:
                        logger.debug("final matched %s" % g)
                    return res
        else:
            logger.debug("no filehandle")
        fp.close() 
        return ('','')     


                
          
def get_file_regex_all(context,regex):
    """ Searches all files that match file regex and searches for regex in contents.
        Returns the contents of groups 'name' and 'unit' as a tuple
    """

    # match fileregex to available files
    #regx = re.compile(fileregex)
    #filename = None
    #for key in context['ready']:
    #    match = regx.match(key)
    #    if match:
    #        filename = key
    #        break

    # FIXME: only handles single file pattern   
    logger.debug("get_file_regex_all") 
    fileregex = context['fileregex'][0]
    logger.debug("fileregex=%s" % fileregex)
    filename = _get_file_from_regex(fileregex,context['ready'],False)
    logger.debug("filename=%s" % filename)
    
    final_res = []
    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return []
    else:
        try:
            fp = _get_file_handle(context, filename)
        except Exception:
            logger.error("bad file handle")
            return []
        if fp:
            regx = re.compile(regex)
            for line in fp:
                match = regx.search(line)
                
                if match:
                    value = match.group('value')
                    logger.debug("value=%s" % value)
                    final_res.append(value.rstrip())
            fp.close()
        logger.debug("final_res=%s" % final_res) 
        return final_res     



    
def get_constant(context,val,unit):
    return (val,unit)

            
def get_metadata(ruleset):
    from collections import defaultdict
    
    # TODO: handle files that have not arrived yet
    expectedmd5 = None
                  
    #TODO: missing values default to STRING, but later could be numeric when have value
    metadatas = {}
    for exp in Experiment.objects.all():
        logger.debug("exp=%s\n" % exp)
        for dataset in Dataset.objects.filter(experiment=exp):
            meta = {}
            logger.debug("\tdataset=%s\n" % dataset)
            ready = defaultdict()
            for datafile in Dataset_File.objects.filter(dataset=dataset):
                logger.debug("\t\tdatafile=%s\n" % str(datafile))
                ready[datafile.filename] = datafile
                if datafile not in ready:
                    logger.debug(datafile.md5sum + "\n")
                    try:
                        datafile._set_md5sum() 
                    except IOError:
                        pass
                    except OSError:
                        pass
                    logger.debug("hello from %s\n" % datafile)
                    #if (datafile.md5sum == datafile.expectedmd5):
                    #    ready[datafile] = True
                    
            logger.debug("ready=%s\n" % ready)
            for tagname,file_patterns,code in ruleset:
                logger.debug("file_patterns=%s,code=%s\n" % (file_patterns,code))
            
                # check whether we have all files available.
                # f could have _number regex
                count = 0
                for file_pattern in file_patterns:
                    import re
                    rule_file_regx = re.compile(file_pattern)
                    filename = None
                    # ready files could have _number prefix
                    for datafilename in ready:
                        match = rule_file_regx.match(datafilename)
                        if match:
                            logger.debug("matched % s" % datafilename)
                            filename = datafilename
                            break
                    logger.debug("filename=%s\n" % filename)
                    if filename in ready:
                        count += 1
                logger.debug("count=%d" % count)
                if count == len(file_patterns):
                    logger.debug("ready to start extracting on %s files\n" % count)
                    data_context = {'expid':exp.id,
                               'ready':ready,
                               'fileregex':file_patterns}
                    logger.debug("data_context=%s" % data_context)
                    try:
                        (value,unit) = eval(code,{},
                                         {"get_file_line":get_file_line,
                                          "get_file_lines":get_file_lines,
                                          "get_file_regex":get_file_regex,
                                          "get_file_regex_all":get_file_regex_all,
                                          "get_regex_lines":get_regex_lines,
                                          "get_regex_lines_vallist":get_regex_lines_vallist,
                                          "get_final_iteration":get_final_iteration,
                                          "get_constant":get_constant,
                                          'context':data_context})
                    except Exception,e:
                        logger.error("Exception %s" % e)
                        logger.debug("value,unit=%s %s" % (value,unit))
                 
                    meta[tagname] = (value,unit)
                     
            logger.debug("meta=%s\n" % meta)
            metadatas[dataset] = meta
        
    return metadatas
        
            
def get_schema(schema,name):
    """Return the schema object that the paramaterset will use.
    """
    try:
        sch = Schema.objects.get(namespace__exact=schema)
        logger.debug("found %s %s" % (sch.namespace, sch.name))
        return sch
    except Schema.DoesNotExist:
        schema = Schema(namespace=schema, name=name,
                        type=Schema.DATASET)
        schema.save()
        logger.debug("creating %s %s " % (schema,name))
        return schema          
            
def get_parameters(schema,metadata):
    
    param_objects = ParameterName.objects.filter(schema=schema)
    logger.debug("param_objects=%s\n" % param_objects)
    parameters = []
    for p in metadata.keys():
        logger.debug("pp=%s\n" % p)
        logger.debug("metadata[pp][0] = %s" % metadata[p][0])
        logger.debug("metadata[pp][1] = %s" % metadata[p][1])
        parameter = filter(lambda x: x.name == p,param_objects)
        logger.debug("pparameter=%s\n" % parameter)
        if parameter:
            parameters.append(parameter[0])
            continue
        datatype = ParameterName.STRING
        units = None
        try:
            int(metadata[p][0])
        except (ValueError,TypeError):
            pass
        else:
            datatype = ParameterName.NUMERIC
            units = str(metadata[p][1])
        try:
            float(metadata[p][0])
        except (ValueError,TypeError):
            pass
        else:
            datatype = ParameterName.NUMERIC
            units = str(metadata[p][1])
        logger.debug("units=%s" % str(metadata[p][1]))
        if units:
            new_param = ParameterName(schema=schema,
                                  name=p,
                                  full_name=p,
                                  data_type=datatype,
                                  units=units)
        else:
            new_param = ParameterName(schema=schema,
                                  name=p,
                                  full_name=p,
                                  data_type=datatype)
        new_param.save()
        logger.debug("new_param=%s" % new_param)
        logger.debug("datatype=%s" % datatype)
        parameters.append(new_param)
    return parameters

def save_metadata(instance,schema,metadata):
    parameters = get_parameters(schema, metadata)
    logger.debug("parameters=%s" % parameters)
    if not parameters:
        return None
    try:
        ps = DatasetParameterSet.objects.get(schema=schema,
                                                dataset=instance)
        #return ps
    except DatasetParameterSet.DoesNotExist:
        ps = DatasetParameterSet(schema=schema,dataset=instance)
        ps.save()
    logger.debug("ps=%s\n" % ps)
    logger.debug("metadata2=%s\n" % metadata)
    for p in parameters:
        logger.debug("p=%s\n" % p)
        if p.name in metadata:
            logger.debug("found p =%s %s\n" % (p.name,p.units))
            
            if p.isNumeric():
                val = metadata[p.name][0]
                if val:
                           
                    try:
                        dfp = DatasetParameter.objects.get(parameterset=ps,name=p)
                    except DatasetParameter.DoesNotExist:           
                        dfp = DatasetParameter(parameterset=ps,
                                    name=p)
                    dfp.numerical_value = val
                    logger.debug("numeric")
                    dfp.save()
            else:
                val = metadata[p.name][0]
                if val:
                    try:
                        dfp = DatasetParameter.objects.get(parameterset=ps,name=p)
                    except DatasetParameter.DoesNotExist:           
                        dfp = DatasetParameter(parameterset=ps,
                                    name=p)
                    dfp.string_value = metadata[p.name][0]
                    dfp.save()
                    logger.debug("string")
            
            
def go():
    for schemainfo in rulesets:
        metadatas = get_metadata(rulesets[schemainfo])
        logger.debug("metadatas=%s\n" % metadatas)
    
        schema = get_schema(schemainfo[0],schemainfo[1])
    
        for metadata in metadatas:
            save_metadata(metadata,schema,metadatas[metadata])

      
                   
