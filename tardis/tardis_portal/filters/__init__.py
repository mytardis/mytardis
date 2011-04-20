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
__init__.py

.. moduleauthor:: Russell Sim <russell.sim@monash.edu>

"""

import logging

from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_save
from django.core.exceptions import MiddlewareNotUsed


logger = logging.getLogger(__name__)


class FilterInitMiddleware(object):
    def __init__(self):
        from tardis.tardis_portal.models import Dataset_File
        for f in settings.POST_SAVE_FILTERS:
            cls = f[0]
            args = []
            kw = {}

            if len(f) == 2:
                args = f[1]

            if len(f) == 3:
                kw = f[2]

            hook = self._safe_import(cls, args, kw)
            # XXX seems to requre a strong ref else it won't fire,
            # could be because some hooks are classes not functions.
            post_save.connect(hook, sender=Dataset_File, weak=False)
            logger.debug('Initialised postsave hook %s' % post_save.receivers)

        # disable middleware
        raise MiddlewareNotUsed()

    def _safe_import(self, path, args, kw):
        try:
            dot = path.rindex('.')
        except ValueError:
            raise ImproperlyConfigured('%s isn\'t a filter module' % path)
        filter_module, filter_classname = path[:dot], path[dot + 1:]
        try:
            mod = import_module(filter_module)
        except ImportError, e:
            raise ImproperlyConfigured('Error importing filter %s: "%s"' %
                                       (filter_module, e))
        try:
            filter_class = getattr(mod, filter_classname)
        except AttributeError:
            raise ImproperlyConfigured('Filter module "%s" does not define a "%s" class' %
                                       (filter_module, filter_classname))

        filter_instance = filter_class(*args, **kw)
        return filter_instance
