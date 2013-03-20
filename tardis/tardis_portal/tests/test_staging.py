# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010, VeRSI Consortium
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
test_views.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>

"""
from os import path

from django.test import TestCase


class TestStagingFiles(TestCase):
    def setUp(self):
        from tardis.tardis_portal import models
        from tempfile import mkdtemp, mktemp
        from django.conf import settings
        import os

        # Disconnect post_save signal
        from django.db.models.signals import post_save
        from tardis.tardis_portal.models import \
            staging_hook, Replica, Location
        post_save.disconnect(staging_hook, sender=Replica)

        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

        try:
            os.makedirs(settings.GET_FULL_STAGING_PATH_TEST)
        except OSError:
            pass
        self.temp = mkdtemp(dir=settings.GET_FULL_STAGING_PATH_TEST)

        self.file = mktemp(dir=self.temp)
        content = 'test file'
        with open(self.file, "w+b") as f:
            f.write(content)

        Location.force_initialize()

        # make datafile
        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                created_by=self.user)
        exp.save()

        # make dataset
        dataset = models.Dataset(description="dataset description...")
        dataset.save()
        dataset.experiments.add(exp)
        dataset.save()

        # create datafile
        df = models.Dataset_File(dataset=dataset, size=len(content),
                                 filename=path.basename(self.file),
                                 md5sum='f20d9f2072bbeb6691c0f9c5099b01f3')
        df.save()

        # create replica
        base_url = 'file://' + settings.GET_FULL_STAGING_PATH_TEST
        location = Location.load_location({
            'name': 'staging-test-yyy', 'url': base_url, 'type': 'external',
            'priority': 10, 'transfer_provider': 'local'})
        replica = models.Replica(datafile=df, url='file://' + self.file,
                                 protocol="staging", location=location)
        replica.verify()
        replica.save()
        self.replica = replica

    def tearDown(self):
        # reconnect post_save signal
        from django.db.models.signals import post_save
        from tardis.tardis_portal.models import staging_hook, Replica
        post_save.connect(staging_hook, sender=Replica)

    def test_stage_replica(self):
        from tardis.tardis_portal import staging

        staging.stage_replica(self.replica)
