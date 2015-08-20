#
# Copyright (c) 2013, Centre for Microscopy and Microanalysis
#   (University of Queensland, Australia)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the University of Queensland nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

"""
Management command to (re-)run the ingestion filters by hand.
"""

import sys
import traceback
import logging
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

from tardis.tardis_portal.models import Experiment, Dataset, DataFile
from tardis.tardis_portal.models import DataFileObject


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = '[<filter-no>] ...'
    help = """Run selected ingestion filters on all Datafiles.
Note that a typical ingestion filter sets a 'flag' parameter in its
Datafile's parameter set to avoid adding multiple copies of the ingested
metadata parameters.  This command cannot override that flag to force
metadata to be reingested."""
    option_list = BaseCommand.option_list + (
        make_option('--dryRun', '-n',
                    action='store_true',
                    dest='dryRun',
                    default=False,
                    help="Don't commit the results of running the " \
                        "filters to the database.  Warning: does not " \
                        "handle non-database changes made by a filter!"),
        ) + (
        make_option('--list', '-l',
                    action='store_true',
                    dest='list',
                    default=False,
                    help="List the ingestion filters configured in "
                         "settings.POST_SAVE_FILTERS"),
        ) + (
        make_option('--all', '-a',
                    action='store_true',
                    dest='all',
                    default=False,
                    help="Run all available filters"),
        )

    def handle(self, *args, **options):
        filterIds = []
        self.availableFilters = settings.POST_SAVE_FILTERS
        if options.get('list'):
            pass
        elif options.get('all'):
            filterIds = range(0, len(self.availableFilters))
        else:
            for arg in args:
                try:
                    id = int(arg) - 1
                except:
                    raise CommandError("Invalid filter-no: '%s'" % arg)
                if id < 0 or id >= len(self.availableFilters):
                    raise CommandError("Invalid filter-no: '%s'" % arg)
                filterIds = filterIds + [id]
        if len(filterIds):
            self.runFilters(self.instantiateFilters(filterIds),
                            dryRun=options['dryRun'])
        else:
            self.listFilters()

    def instantiateFilters(self, filterIds):
        filters = []
        for id in filterIds:
            f = self.availableFilters[id]
            if f and len(f):
                cls = f[0]
                args = []
                kw = {}

                if len(f) >= 2:
                    args = f[1]

                if len(f) >= 3:
                    kw = f[2]
                try:
                    filters += [self._safe_import(cls, args, kw)]
                except ImproperlyConfigured as e:
                    print "Skipping improperly configured filter %s : %s" % \
                        (id + 1, e)
        return filters

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

    def runFilters(self, filters, dryRun=False):
        if dryRun:
            raise Exception("dryRun not supported.")
        try:
            for datafile in DataFile.objects.all():
                dfo = DataFileObject.objects.filter(datafile=datafile,
                                                    verified=True).first()
                if not dfo:
                    continue 
                try:
                    for filter in filters:
                        filter(sender=DataFile, instance=datafile,
                               created=False, using='default')
                except Exception:
                    exc_class, exc, tb = sys.exc_info()
                    new_exc = CommandError("Exception %s has occurred: " % \
                                               (exc or exc_class))
                    raise new_exc.__class__, new_exc, tb
        finally:
            pass

    def listFilters(self):
        if len(self.availableFilters):
            print 'The following filters are available\n'
            for i in range(0, len(self.availableFilters)):
                filter = self.availableFilters[i]
                if len(filter) == 1:
                    print '%d - %s\n' % (i + 1, filter[0])
                elif len(filter) == 2:
                    print '%d - %s, %s\n' % (i + 1, filter[0], filter[1])
                elif len(filter) >= 3:
                    print '%d - %s, %s, %s\n' % (i + 1, filter[0],
                                                 filter[1], filter[2])
        else:
            print 'No filters are available\n'
