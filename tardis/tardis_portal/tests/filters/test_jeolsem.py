from os import path
from unittest import skipIf

import six

from django.test import TransactionTestCase

from ...filters.jeolsem import JEOLSEMFilter
from ...models import User, ObjectACL, Experiment, Dataset, DataFile, \
    DataFileObject, StorageBox
from ...ParameterSetManager import ParameterSetManager

from ..test_download import get_size_and_sha512sum


@skipIf(six.PY3, "The JOEL SEM filter doesn't yet work with Python 3")
class JEOLSEMFilterTestCase(TransactionTestCase):

    def setUp(self):
        # Create test owner without enough details
        username, email, password = ('testuser',
                                     'testuser@example.test',
                                     'password')
        user = User.objects.create_user(username, email, password)

        # Create test experiment and make user the owner of it
        experiment = Experiment(title='Text Experiment',
                                institution_name='Test Uni',
                                created_by=user)
        experiment.save()
        acl = ObjectACL(
            pluginId='django_user',
            entityId=str(user.id),
            content_object=experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        acl.save()

        dataset = Dataset(description='dataset description...')
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()

        base_path = path.join(path.dirname(__file__), 'fixtures')
        s_box = StorageBox.get_default_storage(location=base_path)

        def create_datafile(index):
            testfile = path.join(base_path, 'jeol_sem_test%d.txt' % index)
            size, sha512sum = get_size_and_sha512sum(testfile)

            datafile = DataFile(dataset=dataset,
                                filename=path.basename(testfile),
                                size=size,
                                sha512sum=sha512sum)
            datafile.save()
            dfo = DataFileObject(
                datafile=datafile,
                storage_box=s_box,
                uri=path.basename(testfile))
            dfo.save()

            return DataFile.objects.get(pk=datafile.pk)

        self.dataset = dataset
        self.datafiles = [create_datafile(i) for i in (1, 2)]

    def testJEOLSimple(self):
        JEOLSEMFilter()(None, instance=self.datafiles[0])

        # Check a parameter set was created
        dataset = Dataset.objects.get(id=self.dataset.id)

        self.assertEqual(dataset.getParameterSets().count(), 1)

        # Check all the expected parameters are there
        psm = ParameterSetManager(dataset.getParameterSets()[0])
        self.assertEqual(
            psm.get_param('metadata-filename', True),
            self.datafiles[0].filename)
        self.assertEqual(psm.get_param('instrument', True), 'JCM-5000')
        self.assertEqual(psm.get_param('accel_volt', True), 10.0)
        self.assertEqual(psm.get_param('micron_bar', True), 175.0)
        self.assertEqual(psm.get_param('micron_marker', True), 200)

        # Check we won't create a duplicate dataset
        JEOLSEMFilter()(None, instance=self.datafiles[0])
        dataset = Dataset.objects.get(id=self.dataset.id)
        self.assertEqual(dataset.getParameterSets().count(), 1)

    def testJEOLComplex(self):
        JEOLSEMFilter()(None, instance=self.datafiles[1])

        # Check a parameter set was created
        dataset = Dataset.objects.get(id=self.dataset.id)
        self.assertEqual(dataset.getParameterSets().count(), 1)

        # Check all the expected parameters are there
        psm = ParameterSetManager(dataset.getParameterSets()[0])
        self.assertEqual(
            psm.get_param('metadata-filename', True),
            self.datafiles[1].filename)
        self.assertEqual(psm.get_param('instrument', True), '7001F_TTL')
        self.assertEqual(psm.get_param('accel_volt', True), 15.0)
        self.assertEqual(psm.get_param('micron_bar', True), 213)
        self.assertEqual(psm.get_param('micron_marker', True), 100)

        # Check we won't create a duplicate dataset
        JEOLSEMFilter()(None, instance=self.datafiles[1])
        dataset = Dataset.objects.get(id=self.dataset.id)
        self.assertEqual(dataset.getParameterSets().count(), 1)
