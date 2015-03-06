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
Management command to change the owner of some experiments
"""

import sys
import traceback
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction, DEFAULT_DB_ALIAS

from tardis.tardis_portal.models import Experiment


class Command(BaseCommand):
    args = '<user> <experiment id>...'
    help = 'Change the owner of the experiments.'
    option_list = BaseCommand.option_list + (
        make_option('--dryRun', '-n',
                    action='store_true',
                    dest='dryRun',
                    default=False,
                    help="Only list the experiment(s) to be chowned"),
        ) + (
        make_option('--forUser', '-u',
                    action='store',
                    dest='forUser',
                    default=None,
                    help="The user the experiment(s) currently belong to"),
        ) + (
        make_option('--all', '-a',
                    action='store_true',
                    dest='all',
                    default=False,
                    help="Chown the experiment(s) currently belong --forUser"),
        )

    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError("Expected a user name and some experiment ids")
        try:
            newOwner = User.objects.get(username=args[0])
        except User.DoesNotExist:
            raise CommandError("User %s not found" % args[0])
        forUser = options.get('forUser')
        currentOwner = None
        if forUser:
            try:
                currentOwner = User.objects.get(username=forUser)
            except User.DoesNotExist:
                raise CommandError("User %s not found" % forUser)
        if options.get('all'):
            if not forUser:
                raise CommandError("Require --forUser <name> with --all")
            if len(args) != 1:
                raise CommandError("Experiment id list not allowed with --all")
            ids = Experiment.objects.filter(created_by=currentOwner).\
                values_list('id', flat=True)
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
        transaction.set_autocommit(False, using=using)

        try:
            for id in ids:
                experiment = Experiment.objects.get(id=id)
                experiment.created_by = newOwner
                experiment.save()
            if options.get('dryRun'):
                transaction.rollback(using=using)
            else:
                transaction.commit(using=using)
        except Exception:
            transaction.rollback(using=using)
            exc_class, exc, tb = sys.exc_info()
            new_exc = CommandError("Exception %s has occurred: rolled back "
                                   "transaction" % (exc or exc_class))
            raise new_exc.__class__, new_exc, tb
        finally:
            transaction.set_autocommit(True, using=using)
