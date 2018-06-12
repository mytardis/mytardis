'''
Tests relating to facility overview
'''
import json
from StringIO import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.test import TestCase

from tardis.tardis_portal.models.datafile import DataFile
from tardis.tardis_portal.models.datafile import DataFileObject
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.facility import Facility
from tardis.tardis_portal.models.instrument import Instrument

from tardis.tardis_portal.views.facilities import facility_overview_datafile_list
from tardis.tardis_portal.views.facilities import facility_overview_experiments


class FacilityOverviewTestCase(TestCase):
    def setUp(self):
        username = 'tardis_user1'
        pwd = 'secret'  # nosec
        email = ''
        self.user = User.objects.create_user(username, email, pwd)

        self.exp = Experiment(
            title='test exp1', institution_name='monash',
            created_by=self.user)

        self.exp.save()
        self.exp2 = Experiment(
            title='test exp2', institution_name='monash',
            created_by=self.user)
        self.exp2.save()

        self.group = Group(name="Test Manager Group")
        self.group.save()
        self.group.user_set.add(self.user)
        self.facility = Facility(
            name="Test Facility", manager_group=self.group)
        self.facility.save()
        self.instrument = Instrument(
            name="Test Instrument", facility=self.facility)
        self.instrument.save()

        self.dataset = Dataset(description='test dataset1')
        self.dataset.instrument = self.instrument
        self.dataset.save()
        self.dataset.experiments = [self.exp, self.exp2]
        self.dataset.save()

        def _build(dataset, filename, url):
            datafile_content = "\n".join(['some data %d' % i
                                          for i in range(1000)])
            filesize = len(datafile_content)
            datafile = DataFile(
                dataset=dataset, filename=filename, size=filesize)
            datafile.save()
            dfo = DataFileObject(
                datafile=datafile,
                storage_box=datafile.get_default_storage_box(),
                uri=url)
            dfo.file_object = StringIO(datafile_content)
            dfo.save()
            return datafile

        saved_setting = settings.REQUIRE_DATAFILE_CHECKSUMS
        try:
            settings.REQUIRE_DATAFILE_CHECKSUMS = False
            self.datafile1 = _build(self.dataset, 'file1.txt', 'path/file1.txt')
            self.datafile2 = _build(self.dataset, 'file2.txt', 'path/file2.txt')
            self.datafile3 = _build(self.dataset, 'file3.txt', 'path/file3.txt')
        finally:
            settings.REQUIRE_DATAFILE_CHECKSUMS = saved_setting

    def test_facility_overview_datafile_list(self):
        datafile_list = facility_overview_datafile_list(self.dataset)
        self.assertEqual(
            [file_dict['filename'] for file_dict in datafile_list],
            ['file1.txt', 'file2.txt', 'file3.txt'])

    def test_facility_overview_experiments(self):
        '''
        Despite the name of the test_facility_overview_experiments
        method, it actually returns a JSON list of datasets
        (not experiments)
        '''
        factory = RequestFactory()
        start_index = 0
        end_index = 5
        request = factory.get(
            '/facility/fetch_data/%s/%s/%s/'
            % (self.facility.id, start_index, end_index))
        request.user = self.user
        response = facility_overview_experiments(
            request, self.facility.id, start_index, end_index)
        dataset_list = json.loads(response.content)
        self.assertEqual(
            [dataset['description'] for dataset in dataset_list],
            [self.dataset.description])
