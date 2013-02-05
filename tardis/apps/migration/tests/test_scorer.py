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
from django.conf import settings

from tardis.apps.migration import MigrationScorer
from tardis.apps.migration.models import get_user_priority
from tardis.apps.migration.tests.generate import \
    generate_datafile, generate_dataset, generate_experiment, generate_user
from tardis.tardis_portal.models import Replica, Location

class MigrateScorerTestCase(TestCase):

    def _setup(self):
        self.user1 = generate_user('joe', 2)
        self.user2 = generate_user('fred', 1)
        self.exp1 = generate_experiment(users=[self.user1, self.user2])
        self.exp2 = generate_experiment(users=[self.user1])
        self.exp3 = generate_experiment(users=[self.user1])
        self.exp4 = generate_experiment(users=[self.user1])
        self.ds1 = generate_dataset(experiments=[self.exp1])
        self.ds2 = generate_dataset(experiments=[self.exp1, self.exp2])
        self.ds3 = generate_dataset(experiments=[self.exp3])
        self.ds4 = generate_dataset(experiments=[self.exp4])
        self.df1, self.rep1 = generate_datafile('1/2/1', self.ds1, size=100)
        self.df2, self.rep2 = generate_datafile('1/2/2', self.ds1, size=100, 
                                                verified=False)
        self.df3, self.rep3 = generate_datafile(
            'http://127.0.0.1:4272/data/1/2/3', self.ds1, size=1000)
        self.df4, self.rep4 = generate_datafile('1/2/4', self.ds2, size=1000)
        self.df5, self.rep5 = generate_datafile('1/2/5', self.ds2, size=10000)
        self.df6, self.rep6 = generate_datafile('1/2/6', self.ds3, size=100000)
        self.df7, self.rep7 = generate_datafile('1/2/7', self.ds4, size=0)
        self.df8, self.rep8 = generate_datafile('1/2/8', self.ds4, size=-1)

    def testScoring(self):
        self._setup()
        scorer = MigrationScorer(Location.get_location('local').id)
        self.assertEquals(2.0, scorer.datafile_score(self.df1))
        self.assertEquals(2, get_user_priority(self.user1))
        self.assertEquals(1, get_user_priority(self.user2))
        self.assertEquals(1.0, scorer.user_score(self.user1))
        self.assertEquals(2.0, scorer.user_score(self.user2))
        self.assertEquals(2.0, scorer.experiment_score(self.exp1))
        self.assertEquals(2.0, scorer.dataset_score(self.df1.dataset))
        self.assertEquals(4.0, scorer.score_datafile(self.df1))
        self.assertEquals([(self.df1, self.rep1, 4.0)], 
                          scorer.score_datafiles_in_dataset(self.ds1))
        self.assertEquals([(self.df5, self.rep5, 8.0), 
                           (self.df4, self.rep4, 6.0), 
                           (self.df1, self.rep1, 4.0)],
                          scorer.score_datafiles_in_experiment(self.exp1))
        self.assertEquals([(self.df5, self.rep5, 8.0), 
                           (self.df4, self.rep4, 6.0)],
                          scorer.score_datafiles_in_experiment(self.exp2))
        self.assertEquals([(self.df6, self.rep6, 5.0)],
                          scorer.score_datafiles_in_experiment(self.exp3))
        self.assertEquals([(self.df5, self.rep5, 8.0), 
                           (self.df4, self.rep4, 6.0), 
                           (self.df6, self.rep6, 5.0), 
                           (self.df1, self.rep1, 4.0), 
                           (self.df7, self.rep7, 0.0), 
                           (self.df8, self.rep8, 0.0)],
                          scorer.score_all_datafiles())
        self.assertEquals([(self.df7, self.rep7, 0.0), 
                           (self.df8, self.rep8, 0.0)], 
                          scorer.score_datafiles_in_dataset(self.ds4))

    def testScoringWithTimes(self):
        self._setup()
        scorer = MigrationScorer(
            Location.get_location('local').id, {
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
        rep = Replica.objects.get(pk=self.rep1.pk)
        rep.url = f.name
        rep.save()

        self.assertEquals(2.0, scorer.datafile_score(self.df1))
        
        older = time.time() - (60 * 60 * 24 + 300)
        os.utime(f.name, (older, older))

        self.assertEquals(3.0, scorer.datafile_score(self.df1))

        older = time.time() - (60 * 60 * 24 * 2 + 300)
        os.utime(f.name, (older, older))

        self.assertEquals(5.0, scorer.datafile_score(self.df1))

        f.close()
