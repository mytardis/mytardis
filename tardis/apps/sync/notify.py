# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2012, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2012, VeRSI Consortium
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
notify.py

.. moduleauthor:: Kieran Spear <kispear@gmail.com>
.. moduleauthor:: Shaun O'Keefe <shaun.okeefe.0@gmail.com>

"""
import logging

from django.conf import settings
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template import Context
from django.template.loader import render_to_string
from tardis.tardis_portal.models import Experiment

from .signals import transfer_failed, transfer_completed
from .models import SyncedExperiment


logger = logging.getLogger(__name__)


@receiver(transfer_failed)
def failed(sender, **kwargs):
    logger.debug('Sending experiment failure emails')
    instance = kwargs['instance']
    email_admins(instance, success=False)


@receiver(transfer_completed)
def completed(sender, **kwargs):
    logger.debug('Sending experiment complete emails')
    instance = kwargs['instance']
    email_admins(instance, success=True)


def _get_email_text(synced_exp, success, template='sync/admin_email.txt'):
    result = 'SUCCEEDED' if success else 'FAILED'
    d = {
        'result': result,
        'experiment': synced_exp.experiment,
        'uid': synced_exp.uid,
        'status': synced_exp.status(),
        'site_url': settings.MYTARDIS_SITE_URL,
        'admin_url': '',
        }
    text = render_to_string(template, Context(d))
    (subject, message) = text.split('\n', 1)
    return (subject, message)


def email_users(synced_exp, success):
    pass

def email_admins(synced_exp, success):
    admins = getattr(settings, 'SYNC_ADMINS', [])
    if not admins:
        return
    if success and not getattr(settings, 'SYNC_ADMINS_NOTIFY_ON_SUCCESS', True):
        return
    from_email = settings.SERVER_EMAIL
    (subject, message) = _get_email_text(synced_exp, success)
    send_mail(subject, message, from_email, admins)

