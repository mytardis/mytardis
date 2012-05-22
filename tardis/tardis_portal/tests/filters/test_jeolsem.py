from os import path
from compare import expect, ensure

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from tardis.tardis_portal.filters.jeolsem import JEOLSEMFilter
from tardis.tardis_portal.models import User, UserProfile, \
    ExperimentACL, Experiment, Dataset, Dataset_File
from tardis.tardis_portal.models.parameters import DatasetParameterSet
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager


class JEOLSEMFilterTestCase(TestCase):

    def setUp(self):
        # Create test owner without enough details
        username, email, password = ('testuser',
                                     'testuser@example.test',
                                     'password')
        user = User.objects.create_user(username, email, password)
        profile = UserProfile(user=user, isDjangoAccount=True)
        profile.save()

        # Create test experiment and make user the owner of it
        experiment = Experiment(title='Text Experiment',
                                institution_name='Test Uni',
                                created_by=user)
        experiment.save()
        acl = ExperimentACL(
            pluginId='django_user',
            entityId=str(user.id),
            experiment=experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
        acl.save()

        dataset = Dataset(description='dataset description...')
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()

        def create_datafile(index):
            testfile = path.join(path.dirname(__file__), 'fixtures',
                                 'jeol_sem_test%d.txt' % index)
            datafile = Dataset_File(dataset=dataset,
                                    filename=path.basename(testfile),
                                    url='file://'+path.abspath(testfile),
                                    protocol='file')
            datafile.save()
            return datafile

        self.dataset = dataset
        self.datafiles = [create_datafile(i) for i in (1,2)]


    def testJEOLSimple(self):
        JEOLSEMFilter()(None, instance=self.datafiles[0], created=True)

        dataset = Dataset.objects.get(id=self.dataset.id)
        expect(dataset.getParameterSets().count()).to_equal(1)

        psm = ParameterSetManager(dataset.getParameterSets()[0])
        expect(psm.get_param('instrument', True)).to_equal('JCM-5000')
        expect(psm.get_param('accel_volt', True)).to_equal(10.0)
        expect(psm.get_param('micron_bar', True)).to_equal(175.0)
        expect(psm.get_param('micron_marker', True)).to_equal(200)

    def testJEOLComplex(self):
        JEOLSEMFilter()(None, instance=self.datafiles[1], created=True)

        dataset = Dataset.objects.get(id=self.dataset.id)
        expect(dataset.getParameterSets().count()).to_equal(1)

        psm = ParameterSetManager(dataset.getParameterSets()[0])
        expect(psm.get_param('instrument', True)).to_equal('7001F_TTL')
        expect(psm.get_param('accel_volt', True)).to_equal(15.0)
        expect(psm.get_param('micron_bar', True)).to_equal(213)
        expect(psm.get_param('micron_marker', True)).to_equal(100)

