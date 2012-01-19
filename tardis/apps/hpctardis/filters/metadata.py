# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2012, RMIT e-Research Office
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
import logging

logger = logging.getLogger(__name__)

from tardis.apps.hpctardis.metadata import rulesets
from tardis.apps.hpctardis.metadata import process_datafile
from tardis.apps.hpctardis.metadata import _get_schema
from tardis.apps.hpctardis.metadata import _save_metadata

class MetadataFilter(object):
    """This filter provides extraction of metadata extraction of HPC files

    """
    def __init__(self):
        pass
    
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

        logger.debug("processing rulesets for %s" % instance)
        for schemainfo in rulesets:
            metadata = process_datafile(instance, rulesets[schemainfo])
            logger.debug("extracted metadata = %s" % metadata)
            
            schema = _get_schema(schemainfo[0],schemainfo[1])
    
            logger.debug("schema = %s" % schema)
          
            _save_metadata(instance.dataset,schema,metadata)


def make_filter(name='', schema='', tagsToFind=[], tagsToExclude=[]):
    return MetadataFilter()

make_filter.__doc__ = MetadataFilter.__doc__
