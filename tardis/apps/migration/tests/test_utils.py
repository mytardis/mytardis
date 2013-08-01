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
#    * Neither the name of the  University of Queensland nor the
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

from django.test import TestCase

import os, urllib2
from os.path import exists
from urllib2 import HTTPError, URLError, urlopen

from tardis.tardis_portal.models import Dataset_File, Replica, Location, \
    Experiment, Dataset
from tardis.tardis_portal.tests.transfer.generate import \
    generate_datafile, generate_dataset, generate_experiment, generate_user

from tardis.apps.migration import remove_experiment, remove_experiment_data
from tardis.apps.migration.models import Archive

class UtilsTestCase(TestCase):

    def setUp(self):
        self.user = generate_user('fred')
        Location.force_initialize()

    def tearDown(self):
        self.user.delete()

    def _build(self):
        self.experiment = generate_experiment(
            users=[self.user],
            title='Meanwhile, down in the archives ...',
            url='http://example.com/something')
        self.experiment2 = generate_experiment(
            users=[self.user],
            title='Meanwhile, behind the potting shed ...',
            url='http://example.com/other')
        self.dataset = generate_dataset(experiments=[self.experiment])
        self.dataset2 = generate_dataset(experiments=[self.experiment])
        self.datafile, self.replica = generate_datafile(
            None, self.dataset, "Hi mum")
        self.datafile2, self.replica2 = generate_datafile(
            None, self.dataset2, "Hello father")

    def _clear(self):
        if self.dataset.id:
            self.dataset.delete()
        if self.dataset2.id:
            self.dataset2.delete()
        if self.experiment.id:
            self.experiment.delete()
        if self.experiment2.id:
            self.experiment2.delete()

    def testRemoveExperimentData(self):
        # First with no sharing
        self._build()
        archive_location = Location.get_location('archtest')
        try:
            nos_experiments = Experiment.objects.count()
            nos_datasets = Dataset.objects.count()
            nos_datafiles = Dataset_File.objects.count()
            nos_replicas = Replica.objects.count()
            self.assertTrue(exists(self.replica.get_absolute_filepath()))
            remove_experiment_data(self.experiment, 
                                   'http://example.com/some.tar.gz',
                                   archive_location)
            self.assertEquals(nos_experiments, Experiment.objects.count())
            self.assertEquals(nos_datasets, Dataset.objects.count())
            self.assertEquals(nos_datafiles, Dataset_File.objects.count())
            self.assertEquals(nos_replicas, Replica.objects.count())
            new_replica = self.datafile.get_preferred_replica()
            self.assertTrue(self.replica.id != new_replica.id)
            self.assertFalse(new_replica.stay_remote)
            self.assertTrue(new_replica.verified)
            self.assertEqual(self.replica.protocol, new_replica.protocol)
            self.assertEqual(archive_location.id, new_replica.location.id)
            self.assertEqual('http://example.com/some.tar.gz#1/1/1',
                             new_replica.url)
            self.assertFalse(exists(self.replica.get_absolute_filepath()))
        finally:
            self._clear()

        # (Check that the deletes cascaded ... )
        self.assertEquals(0, Dataset_File.objects.count())
        self.assertEquals(0, Replica.objects.count())
        
        # Repeat, but with the first dataset in 2 experiments.
        self._build()
        self.dataset.experiments.add(self.experiment2)
        archive_location = Location.get_location('archtest')
        try:
            nos_experiments = Experiment.objects.count()
            nos_datasets = Dataset.objects.count()
            nos_datafiles = Dataset_File.objects.count()
            nos_replicas = Replica.objects.count()
            self.assertTrue(exists(self.replica.get_absolute_filepath()))
            remove_experiment_data(self.experiment, 
                                   'http://example.com/some.tar.gz',
                                   archive_location)
            self.assertEquals(nos_experiments, Experiment.objects.count())
            self.assertEquals(nos_datasets, Dataset.objects.count())
            self.assertEquals(nos_datafiles, Dataset_File.objects.count())
            self.assertEquals(nos_replicas, Replica.objects.count())
            new_replica = self.datafile.get_preferred_replica()
            self.assertTrue(self.replica.id == new_replica.id)
            self.assertTrue(exists(self.replica.get_absolute_filepath()))
            self.assertFalse(exists(self.replica2.get_absolute_filepath()))
        finally:
            self._clear()

        
    def testRemoveExperiment(self):
        # First with no sharing
        self._build()
        archive_location = Location.get_location('archtest')
        try:
            self.assertTrue(exists(self.replica.get_absolute_filepath()))
            remove_experiment(self.experiment) 
            self.assertEquals(1, Experiment.objects.count())
            self.assertEquals(0, Dataset.objects.count())
            self.assertEquals(0, Dataset_File.objects.count())
            self.assertEquals(0, Replica.objects.count())
            self.assertFalse(exists(self.replica.get_absolute_filepath()))
        finally:
            self._clear()

        # (Check that the deletes cascaded ... )
        self.assertEquals(0, Dataset_File.objects.count())
        self.assertEquals(0, Replica.objects.count())
        
        # Repeat, but with the first dataset in 2 experiments.
        self._build()
        self.dataset.experiments.add(self.experiment2)
        archive_location = Location.get_location('archtest')
        try:
            self.assertTrue(exists(self.replica.get_absolute_filepath()))
            remove_experiment(self.experiment) 
            self.assertEquals(1, Experiment.objects.count())
            self.assertEquals(1, Dataset.objects.count())
            self.assertEquals(1, Dataset_File.objects.count())
            self.assertEquals(1, Replica.objects.count())
            new_replica = self.datafile.get_preferred_replica()
            self.assertTrue(self.replica.id == new_replica.id)
            self.assertTrue(exists(self.replica.get_absolute_filepath()))
            self.assertFalse(exists(self.replica2.get_absolute_filepath()))
        finally:
            self._clear()
