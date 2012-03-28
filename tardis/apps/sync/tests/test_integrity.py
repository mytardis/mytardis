from django.contrib.auth.models import User
from django.test import TestCase
from os import path

from tardis.tardis_portal.models import Experiment, Dataset, Dataset_File

from ..integrity import IntegrityCheck


class IntegrityCheckTestCase(TestCase):
    def _make_dataset(self, exp, filenames):
        dataset = Dataset(experiment=exp)
        dataset.save()
        for filename in filenames:
            df = Dataset_File(dataset=dataset, size=41, protocol='file')
            df.filename = filename
            df.url = 'file://' + path.join(path.dirname(__file__), 'data', df.filename)
            df.save()

    def setUp(self):
        self.user = User(username='user1', password='password', email='a@a.com')
        self.user.save()
        self.bad_exp = Experiment(
                approved = True,
                title = 'title1',
                institution_name = 'institution1',
                description = 'description1',
                created_by = self.user,
                public_access = Experiment.PUBLIC_ACCESS_FULL
                )
        self.bad_exp.save()
        self.bad_dataset = self._make_dataset(self.bad_exp, [
            'file_that_exists',
            'file_that_exists_too',
            'file_that_exists_but_is_empty',
            'file_that_doesnt_exist',
            ])

        self.good_exp = Experiment(
                approved = True,
                title = 'title1',
                institution_name = 'institution1',
                description = 'description1',
                created_by = self.user,
                public_access = Experiment.PUBLIC_ACCESS_FULL
                )
        self.good_exp.save()
        self.good_dataset = self._make_dataset(self.good_exp, [
            'file_that_exists',
            'file_that_exists_too'
            ])

    def testBadExperimentFails(self):
        result = IntegrityCheck(self.bad_exp).get_datafiles_integrity()
        self.assertEqual(result['files_ok'], 2)
        self.assertEqual(result['files_incomplete'], 1)
        self.assertEqual(result['files_missing'], 1)

        good_or_bad = IntegrityCheck(self.bad_exp).all_files_complete()
        self.assertFalse(good_or_bad)

    def testGoodExperimentPasses(self):
        result = IntegrityCheck(self.good_exp).get_datafiles_integrity()
        self.assertEqual(result['files_ok'], 2)
        self.assertEqual(result['files_incomplete'], 0)
        self.assertEqual(result['files_missing'], 0)

        good_or_bad = IntegrityCheck(self.good_exp).all_files_complete()
        self.assertTrue(good_or_bad)

