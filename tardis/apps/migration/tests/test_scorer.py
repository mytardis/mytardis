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

import os
from StringIO import StringIO

from django.test import TestCase
from django.contrib.auth.models import User

from tardis.tardis_portal.models import \
    Dataset_File, Dataset, Experiment, UserProfile, ExperimentACL

from tardis.apps.migration import MigrationScorer
from tardis.apps.migration.models import UserPriority

class MigrateScorerTestCase(TestCase):

    def testScoring(self):
        user1 = self._generate_user('joe', 2)
        user2 = self._generate_user('fred', 1)
        exp1 = self._generate_experiment([user1, user2])
        exp2 = self._generate_experiment([user1])
        exp3 = self._generate_experiment([user1])
        ds1 = self._generate_dataset([exp1])
        ds2 = self._generate_dataset([exp1, exp2])
        ds3 = self._generate_dataset([exp3])
        df1 = self._generate_datafile('1/2/1', 100, ds1)
        df2 = self._generate_datafile('1/2/2', 100, ds1, verified=False)
        df3 = self._generate_datafile('http://foo.com/1/2/3', 1000, ds1)
        df4 = self._generate_datafile('1/2/4', 1000, ds2)
        df5 = self._generate_datafile('1/2/5', 10000, ds2)
        df6 = self._generate_datafile('1/2/6', 100000, ds3)
        scorer = MigrationScorer()
        self.assertEquals(4.0, scorer.score_datafile(df1))
        self.assertEquals([(df1, 4.0)], 
                          scorer.score_datafiles_in_dataset(ds1))
        self.assertEquals([(df5, 8.0), (df4, 6.0), (df1, 4.0)],
                          scorer.score_datafiles_in_experiment(exp1))
        self.assertEquals([(df5, 8.0), (df4, 6.0)],
                          scorer.score_datafiles_in_experiment(exp2))
        self.assertEquals([(df6, 5.0)],
                          scorer.score_datafiles_in_experiment(exp3))
        self.assertEquals([(df5, 8.0), (df4, 6.0), (df6, 5.0), (df1, 4.0)],
                          scorer.score_all_datafiles())
        pass

    def _generate_datafile(self, path, size, dataset, verified=True):
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
        if priority != 2:
            UserPriority(user=user,priority=priority).save()
        return user
