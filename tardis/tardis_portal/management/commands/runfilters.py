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
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction, DEFAULT_DB_ALIAS

from tardis.tardis_portal.models import Experiment, Dataset, Dataset_File


class Command(BaseCommand):
    args = '[<filter-no>] ...'
    help = 'Run selected ingestion filters on all Datafiles.'
    option_list = BaseCommand.option_list + (
        make_option('--list', '-l',
                    action='store_true',
                    dest='list',
                    default=False,
                    help="List the filters configured in"
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
        if options.get('list'):
            pass
        elif options.get('all'):
            filterIds = range(1, len(settings.POST_SAVE_FILTERS))
        else:
            for arg in args:
                try:
                    no = int(arg)
                except:
                    raise CommandError("Invalid filter-no: '%s'" % arg)
                if no <= 0 or no > len(settings.POST_SAVE_FILTERS):
                    raise CommandError("Invalid filter-no: '%s'" % arg)
                filterIds = filterIds + [no]
        if len(filterIds):
            self.runFilters(instantiateFilters(filterIds))
        else:
            self.listFilters()

    def instantiateFilters(self, filterIds):
        filters = []
        for id in filterIds:
            f = settings.POST_SAVE_FILTERS[id - 1]
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
                    print "Skipping improperly configured filter %s : %s" %\
                        (id, e)
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
            

    def runFilters(self, filters):
        pass

    def listFilters(self):
        for i in range(1, len(settings.POST_SAVE_FILTERS)):
            filter = settings.POST_SAVE_FILTERS[i - 1]
            if len(filter) == 1:
                print '%d - %s\n' % (i, filter[0])
            elif len(filter) == 2:
                print '%d - %s, %s\n' % (i, filter[0], filter[1])
            elif len(filter) >= 3:
                print '%d - %s, %s, %s\n' % (i, filter[0], 
                                             filter[1], filter[2])
        else:
            ids = []
            for arg in args[1:]:
                try:
                    id = int(arg)
                    experiment = Experiment.objects.get(id=id)
                    if currentOwner and experiment.created_by != currentOwner:
                        raise CommandError("Experiment %s is not currently "
                                           "owned by %s" % (id, forUser))
                    ids.append(id)
                except Experiment.DoesNotExist:
                    raise CommandError("Experiment %s does not exist" % id)
                except ValueError:
                    raise CommandError("Experiment id (%s) not a number" % arg)
                
        using = options.get('database', DEFAULT_DB_ALIAS)
        transaction.commit_unless_managed(using=using)
        transaction.enter_transaction_management(using=using)
        transaction.managed(True, using=using)

        try:
            for id in ids:
                experiment = Experiment.objects.get(id=id)
                experiment.created_by = newOwner
                experiment.save()
            if options.get('dryRun'):
                transaction.rollback(using=using)
            else:
                transaction.commit(using=using)
            transaction.leave_transaction_management(using=using)
        except Exception:
            transaction.rollback(using=using)
            exc_class, exc, tb = sys.exc_info()
            new_exc = CommandError("Exception %s has occurred: rolled back "
                                   "transaction" % (exc or exc_class))
            raise new_exc.__class__, new_exc, tb

