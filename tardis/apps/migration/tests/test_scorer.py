import os
from StringIO import StringIO

from django.test import TestCase
from django.contrib.auth.models import User

from tardis.tardis_portal.models import \
    Dataset_File, Dataset, Experiment, UserProfile, ExperimentACL

from tardis.apps.migration import MigrationScorer

class MigrateScorerTestCase(TestCase):

    def testScoring(self):
        user1 = self._generate_user('ron')
        user2 = self._generate_user('eunice')
        exp1 = self._generate_experiment([user1, user2])
        exp2 = self._generate_experiment([user1])
        ds1 = self._generate_dataset([exp1])
        ds2 = self._generate_dataset([exp1, exp2])
        df1 = self._generate_datafile('1/2/1', 100, ds1)
        df2 = self._generate_datafile('1/2/2', 100, ds1, verified=False)
        df3 = self._generate_datafile('http://foo.com/1/2/3', 1000, ds1)
        df4 = self._generate_datafile('1/2/4', 1000, ds2)
        df5 = self._generate_datafile('1/2/5', 10000, ds2)
        scorer = MigrationScorer()
        self.assertEquals(2.0, scorer.score_datafile(df1))
        self.assertEquals([(df1, 2.0,)], 
                          scorer.score_datafiles_in_dataset(ds1))
        self.assertEquals([(df1, 2.0,), (df4, 3.0), (df5, 4.0)],
                          scorer.score_datafiles_in_experiment(exp1))
        self.assertEquals([(df4, 3.0), (df5, 4.0)],
                          scorer.score_datafiles_in_experiment(exp2))
        self.assertEquals([(df1, 2.0,), (df4, 3.0), (df5, 4.0)],
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

    def _generate_user(self, name):
        user = User(username=name)
        user.save()
        UserProfile(user=user).save()
        return user
