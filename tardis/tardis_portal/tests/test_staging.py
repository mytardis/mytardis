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
# for skiptest:
# pylint: disable=W0101
from os import path

from django.test import TestCase

from nose.plugins.skip import SkipTest


class TestStagingFiles(TestCase):
    def setUp(self):
        raise SkipTest  # temporarily disabling this feature, needs coding
        from tempfile import mkdtemp, mktemp
        from django.conf import settings
        import os

        # Disconnect post_save signal
        from django.db.models.signals import post_save
        from tardis.tardis_portal.models import Experiment, \
            staging_hook, Dataset, DataFile, DataFileObject, StorageBox
        post_save.disconnect(staging_hook, sender=DataFileObject)

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

        self.filepath = mktemp(dir=self.temp)
        content = 'test file'
        with open(self.filepath, "w+b") as f:
            f.write(content)

        # make datafile
        exp = Experiment(title='test exp1',
                         institution_name='monash',
                         created_by=self.user)
        exp.save()

        # make dataset
        dataset = Dataset(description="dataset description...")
        dataset.save()
        dataset.experiments.add(exp)
        dataset.save()

        # create datafile
        df = DataFile(dataset=dataset, size=len(content),
                      filename=path.basename(self.file),
                      md5sum='f20d9f2072bbeb6691c0f9c5099b01f3')
        df.save()

        # create replica
        base_url = settings.GET_FULL_STAGING_PATH_TEST
        df.dataset.storage_boxes.add(
            StorageBox.get_default_storage(location=base_url))
        dfo = DataFileObject(datafile=df,
                             uri=self.filepath,
                             storage_box=df.dataset.storage_boxes.all()[-1])
        dfo.save()
        self.dfo = dfo

    def tearDown(self):
        # reconnect post_save signal
        from django.db.models.signals import post_save
        from tardis.tardis_portal.models import staging_hook, DataFileObject
        post_save.connect(staging_hook, sender=DataFileObject)

    def test_stage_replica(self):
        from tardis.tardis_portal import staging

        staging.stage_replica(self.dfo)
