import os
from StringIO import StringIO

from django.test import TestCase
from django.contrib.auth.models import User

from tardis.tardis_portal.models import \
    Dataset_File, Dataset, Experiment, UserProfile

from tardis.apps.migration import MigrationScorer

class MigrateScorerTestCase(TestCase):

    def testScoring(self):
        user1 = self._generate_user('ron')
        user2 = self._generate_user('eunice')
        exp1 = self._generate_experiment([user1, user2])
        ds1 = self._generate_dataset([exp1])
        df1 = self._generate_datafile('1/2/foo', 100, ds1)
        df2 = self._generate_datafile('1/2/bar', 100, ds1, verified=False)
        df3 = self._generate_datafile('http://foo.com/1/2/foo', 1000, ds1)
        scorer = MigrationScorer()
        self.assertEquals(2.0, scorer.score_datafile(df1))
        self.assertEquals([(df1, 2.0,)], 
                          scorer.score_datafiles_in_dataset(ds1))
        self.assertEquals([(df1, 2.0,)],
                          scorer.score_datafiles_in_experiment(exp1))
        self.assertEquals([(df1, 2.0,)],
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
        dataset.experiments.extend(experiments)
        dataset.save()
        return dataset

    def _generate_experiment(self, users):
        experiment = Experiment(created_by=users[0])
        experiment.save()
        return experiment

    def _generate_user(self, name):
        user = User(username=name)
        user.save()
        UserProfile(user=user).save()
        return user
