#
# Copyright (c) 2012, Centre for Microscopy and Microanalysis
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

import os, tempfile, time
from StringIO import StringIO

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from tardis.tardis_portal.models import \
    Dataset_File, Dataset, Experiment, UserProfile, ExperimentACL

from tardis.apps.migration import MigrationScorer
from tardis.apps.migration.models import UserPriority, DEFAULT_USER_PRIORITY, \
   get_user_priority

class MigrateScorerTestCase(TestCase):

    def _setup(self):
        self.user1 = self._generate_user('joe', 2)
        self.user2 = self._generate_user('fred', 1)
        self.exp1 = self._generate_experiment([self.user1, self.user2])
        self.exp2 = self._generate_experiment([self.user1])
        self.exp3 = self._generate_experiment([self.user1])
        self.exp4 = self._generate_experiment([self.user1])
        self.ds1 = self._generate_dataset([self.exp1])
        self.ds2 = self._generate_dataset([self.exp1, self.exp2])
        self.ds3 = self._generate_dataset([self.exp3])
        self.ds4 = self._generate_dataset([self.exp4])
        self.df1 = self._generate_datafile('1/2/1', 100, self.ds1)
        self.df2 = self._generate_datafile(
            '1/2/2', 100, self.ds1, verified=False)
        self.df3 = self._generate_datafile(
            'http://foo.com/1/2/3', 1000, self.ds1)
        self.df4 = self._generate_datafile('1/2/4', 1000, self.ds2)
        self.df5 = self._generate_datafile('1/2/5', 10000, self.ds2)
        self.df6 = self._generate_datafile('1/2/6', 100000, self.ds3)
        self.df7 = self._generate_datafile('1/2/7', 0, self.ds4)
        self.df8 = self._generate_datafile('1/2/8', -1, self.ds4)

    def testScoring(self):
        self._setup()
        scorer = MigrationScorer()
        self.assertEquals(2.0, scorer.datafile_score(self.df1))
        self.assertEquals(2, get_user_priority(self.user1))
        self.assertEquals(1, get_user_priority(self.user2))
        self.assertEquals(1.0, scorer.user_score(self.user1))
        self.assertEquals(2.0, scorer.user_score(self.user2))
        self.assertEquals(2.0, scorer.experiment_score(self.exp1))
        self.assertEquals(2.0, scorer.dataset_score(self.df1.dataset))
        self.assertEquals(4.0, scorer.score_datafile(self.df1))
        self.assertEquals([(self.df1, 4.0)], 
                          scorer.score_datafiles_in_dataset(self.ds1))
        self.assertEquals([(self.df5, 8.0), (self.df4, 6.0), (self.df1, 4.0)],
                          scorer.score_datafiles_in_experiment(self.exp1))
        self.assertEquals([(self.df5, 8.0), (self.df4, 6.0)],
                          scorer.score_datafiles_in_experiment(self.exp2))
        self.assertEquals([(self.df6, 5.0)],
                          scorer.score_datafiles_in_experiment(self.exp3))
        self.assertEquals([(self.df5, 8.0), (self.df4, 6.0), (self.df6, 5.0), 
                           (self.df1, 4.0), (self.df7, 0.0), (self.df8, 0.0)],
                          scorer.score_all_datafiles())
        self.assertEquals([(self.df7, 0.0), (self.df8, 0.0)], 
                          scorer.score_datafiles_in_dataset(self.ds4))

    def testScoringWithTimes(self):
        self._setup()
        scorer = MigrationScorer({
                'user_priority_weighting': [5.0, 2.0, 1.0, 0.5, 0.2],
                'file_size_weighting': 1.0,
                'file_access_weighting': 1.0,
                'file_age_weighting': 1.0,
                'file_size_threshold': 0,
                'file_access_threshold': 0,
                'file_age_threshold': 1})
        
        self.assertEquals(0.0, scorer.datafile_score(self.df1))
     
        f = tempfile.NamedTemporaryFile(dir=settings.FILE_STORE_PATH)
        f.write("Hi Mom!!\n")
        self.df1.url = f.name

        self.assertEquals(2.0, scorer.datafile_score(self.df1))
        
        older = time.time() - (60 * 60 * 24 + 300)
        os.utime(f.name, (older, older))

        self.assertEquals(3.0, scorer.datafile_score(self.df1))

        older = time.time() - (60 * 60 * 24 * 2 + 300)
        os.utime(f.name, (older, older))

        self.assertEquals(5.0, scorer.datafile_score(self.df1))

        f.close()

    def _generate_datafile(self, path, size, dataset, \
                               verified=True):
        datafile = Dataset_File()
        datafile.url = path
        datafile.mimetype = "application/unspecified"
        datafile.filename = os.path.basename(path)
        datafile.dataset_id = dataset.id
        datafile.size = size
        datafile.verified = verified
        datafile.save()
        return datafile

    def _generate_dataset(self, experiments):
        dataset = Dataset()
        dataset.save()
        for exp in experiments:
            dataset.experiments.add(exp)
        dataset.save()
        return dataset

    def _generate_experiment(self, users):
        experiment = Experiment(created_by=users[0])
        experiment.save()
        for user in users:
            acl = ExperimentACL(experiment=experiment,
                                pluginId='django_user',
                                entityId=str(user.id),
                                isOwner=True,
                                canRead=True,
                                canWrite=True,
                                canDelete=True,
                                aclOwnershipType=ExperimentACL.OWNER_OWNED)
            acl.save()
        return experiment

    def _generate_user(self, name, priority):
        user = User(username=name)
        user.save()
        UserProfile(user=user).save()
        if priority != DEFAULT_USER_PRIORITY:
            UserPriority(user=user,priority=priority).save()
        return user
