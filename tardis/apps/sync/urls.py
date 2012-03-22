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
urls.py

.. moduleauthor:: Kieran Spear <kispear@gmail.com>
.. moduleauthor:: Shaun O'Keefe <shaun.okeefe.0@gmail.com>

"""
from django.conf.urls.defaults import patterns, include, url


# urls that present the API for the consumer to make requests to
# and query the provider about the status of transfers
provider_urls = patterns(
            'tardis.apps.sync.views',
            url(r'^get/', 'get_experiment', name='sync-get-experiment'),
            url(r'^status/(?P<uid>[\w\.\-]+)/', 'transfer_status', name='sync-transfer-status'),
        )

# urls that present the API for the provider to inform the consumer
# about new ingestions etc..
consumer_urls = patterns(
            'tardis.apps.sync.views',
            (r'^notify_experiment/(?P<uid>\d+)/$', 'notify_experiment'),
        )

interface_urls = patterns(
            'tardis.apps.sync.views',
            (r'^index/(?P<experiment_id>\d+)/$', 'index'),
)

urlpatterns = patterns('',
                       (r'^provider/', include(provider_urls)),
                       (r'^consumer/', include(consumer_urls)),
                       (r'^experiments/', include(interface_urls)),
                       )
