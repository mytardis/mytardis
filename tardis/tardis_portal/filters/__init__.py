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

from tardis.tardis_portal.models.datafile import DataFileObject

logger = logging.getLogger(__name__)


class FilterInitMiddleware(object):

    def __init__(self, filters=None):  # noqa # TODO too complex
        from tardis.tardis_portal.models import DataFile
        if not filters:
            filters = getattr(settings, 'POST_SAVE_FILTERS', [])
        for f in filters:
            cls = f[0]
            args = []
            kw = {}

            if len(f) >= 2:
                args = f[1]

            if len(f) >= 3:
                kw = f[2]

            # This hook dispatches a datafile save to a datafile filter.
            # We only dispatch to the filter if the datafile's preferred
            # replica is verified.
            def make_datafile_hook(dfh):
                def datafile_hook(**kw):
                    datafile = kw.get('instance')
                    if datafile.get_preferred_replica(verified=True):
                        dfh(**kw)
                return datafile_hook
            datafile_hook = make_datafile_hook(
                self._safe_import(cls, args, kw))

            # This dispatches a replica save to a datafile filter if the
            # replica is now in 'verified' state.
            def make_dfo_hook(dfh):
                def dfo_hook(**kw):
                    dfo = kw.get('instance')
                    if dfo.verified:
                        kw['instance'] = dfo.datafile
                        kw['dfo'] = dfo  # not actually needed it seems
                        kw['sender'] = DataFile
                        dfh(**kw)
                return dfo_hook

            # XXX seems to requre a strong ref else it won't fire,
            # could be because some hooks are classes not functions.
            # Need to use dispatch_uid to avoid expensive duplicate signals.
            # https://docs.djangoproject.com/en/dev/topics/signals/#preventing-duplicate-signals # noqa # long url
            post_save.connect(datafile_hook, sender=DataFile,
                              weak=False, dispatch_uid=cls + ".datafile")
            post_save.connect(make_dfo_hook(datafile_hook),
                              sender=DataFileObject,
                              weak=False, dispatch_uid=cls + ".dfo")
            logger.debug('Initialised postsave hooks %s' % post_save.receivers)

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
            raise ImproperlyConfigured(
                'Filter module "%s" does not define a "%s" class' %
                (filter_module, filter_classname))

        filter_instance = filter_class(*args, **kw)
        return filter_instance
