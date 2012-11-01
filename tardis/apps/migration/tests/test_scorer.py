import os
from StringIO import StringIO

from django.test import TestCase
from django.contrib.auth.models import User

from tardis.tardis_portal.models import \
    Dataset_File, Dataset, Experiment, UserProfile

from tardis.apps.migration import MigrationScorer

class MigrateScorerTestCase(TestCase):

    def setUp(self):
        self.dummy_dataset = Dataset()
        self.dummy_dataset.save()
        self.dummy_user = self._generate_user()

    def tearDown(self):
        self.dummy_dataset.delete()
        self.dummy_user.delete()

    def testScoring(self):
        scorer = MigrationScorer()
        pass

    def _generate_datafile(self, path, size, dataset, verified=True):
        datafile = Dataset_File()
        datafile.url = path
        datafile.mimetype = "application/unspecified"
        datafile.filename = os.path.basename(filepath)
        datafile.dataset_id = self.dataset.id
        datafile.size = size
        datafile.verified = verified
        datafile.save()
        return datafile

    def _generate_dataset(self, experiments):
        dataset = Dataset()
        dataset.save()

    def _generate_experiment(self, users):
        experiment = Experiment(created_by=users[0])
        experiment.save()

    def _generate_user(self):
        user = User(username='jim',
                    first_name='James',
                    last_name='Spriggs',
                    email='jim.spriggs@goonshow.com')
        user.save()
        UserProfile(user=user).save()
        return user
