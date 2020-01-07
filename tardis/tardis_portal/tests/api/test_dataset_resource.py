'''
Testing the Dataset resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''

import json

from urllib.parse import quote

from ...models.datafile import DataFile
from ...models.dataset import Dataset
from ...models.experiment import Experiment
from ...models.instrument import Instrument

from . import MyTardisResourceTestCase


class DatasetResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(DatasetResourceTest, self).setUp()
        self.extra_instrument = Instrument()
        self.extra_instrument = Instrument(name="Extra Instrument",
                                           facility=self.testfacility)
        self.extra_instrument.save()
        self.ds_no_instrument = Dataset()
        self.ds_no_instrument.description = "Dataset no instrument"
        self.ds_no_instrument.save()
        self.ds_no_instrument.experiments.add(self.testexp)
        self.ds_with_instrument = Dataset()
        self.ds_with_instrument.description = "Dataset with instrument"
        self.ds_with_instrument.instrument = self.testinstrument
        self.ds_with_instrument.save()
        self.ds_with_instrument.experiments.add(self.testexp)
        self.ds_with_instrument2 = Dataset()
        self.ds_with_instrument2.description = "Dataset with a different instrument"
        self.ds_with_instrument2.instrument = self.extra_instrument
        self.ds_with_instrument2.save()
        self.ds_with_instrument2.experiments.add(self.testexp)

    def test_get_dataset_no_instrument(self):
        uri = '/api/v1/dataset/?description=%s' \
            % quote(self.ds_no_instrument.description)
        output = self.api_client.get(uri,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        self.assertTrue('description' in returned_object)
        self.assertEqual(returned_object['description'],
                         self.ds_no_instrument.description)
        self.assertTrue('instrument' in returned_object)
        self.assertIsNone(returned_object['instrument'])

    def test_get_dataset_with_instrument(self):
        uri = '/api/v1/dataset/?description=%s' \
            % quote(self.ds_with_instrument.description)
        output = self.api_client.get(uri,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        self.assertTrue('description' in returned_object)
        self.assertEqual(returned_object['description'],
                         self.ds_with_instrument.description)
        self.assertTrue('instrument' in returned_object)
        self.assertTrue('id' in returned_object['instrument'])
        self.assertEqual(returned_object['instrument']['id'],
                         self.testinstrument.id)

    def test_get_dataset_filter_instrument(self):
        uri = '/api/v1/dataset/?instrument=%s' \
            % self.extra_instrument.id
        output = self.api_client.get(uri,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        self.assertTrue('instrument' in returned_object)
        self.assertTrue('id' in returned_object['instrument'])
        self.assertEqual(returned_object['instrument']['id'],
                         self.extra_instrument.id)

    def test_post_dataset(self):
        exp_id = Experiment.objects.first().id
        post_data = {
            "description": "api test dataset",
            "experiments": [
                "/api/v1/experiment/%d/" % exp_id,
            ],
            "immutable": False}
        dataset_count = Dataset.objects.count()
        response = self.api_client.post(
            '/api/v1/dataset/',
            data=post_data,
            authentication=self.get_credentials())
        self.assertHttpCreated(response)
        self.assertEqual(dataset_count + 1, Dataset.objects.count())
        created_dataset_uri = response['Location']
        created_dataset_id = created_dataset_uri.split('/')[-2]
        created_dataset = Dataset.objects.get(id=created_dataset_id)
        self.assertEqual(created_dataset.experiments.count(), 1)
        self.assertEqual(
            created_dataset.experiments.first().id, exp_id)

    def test_get_dataset_files(self):
        ds_id = self.ds_no_instrument.id
        uri = '/api/v1/dataset/%d/files/' % ds_id
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data['meta']['total_count'], 0)

    def test_get_root_dir_nodes(self):
        dataset = Dataset.objects.create(description='test dataset')
        uri = '/api/v1/dataset/%d/root-dir-nodes/' % dataset.id
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data, [])

        DataFile.objects.create(
            dataset=dataset, filename='filename2',
            size=0, algorithm='md5', checksum='bogus',
            directory='subdir')
        DataFile.objects.create(
            dataset=dataset, filename='filename1',
            size=0, algorithm='md5', checksum='bogus')

        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        # The children list in the 'subdir' node is empty below,
        # because the root-dir-nodes API endpoint is designed to
        # only show files and folders immediately within the dataset's
        # top-level directory:
        expected_data = [
            {
                'name': 'filename1'

            },
            {
                'name': 'subdir',
                'path': 'subdir',
                'children' : []
            }
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x['name']),
            sorted(expected_data, key=lambda x: x['name'])
        )

        dataset.delete()

    def test_get_child_dir_nodes(self):
        dataset = Dataset.objects.create(description='test dataset')
        uri = '/api/v1/dataset/%d/child-dir-nodes/?dir_path=subdir' % dataset.id
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data, [])

        DataFile.objects.create(
            dataset=dataset, filename='filename1',
            size=0, algorithm='md5', checksum='bogus',
            directory='subdir')
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data, [
            {
                'name': 'filename1'
            }
        ])

        DataFile.objects.create(
            dataset=dataset, filename='filename2',
            size=0, algorithm='md5', checksum='bogus',
            directory='subdir')
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        expected_data = [
            {
                'name': 'filename1'

            },
            {
                'name': 'filename2'
            }
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x['name']),
            sorted(expected_data, key=lambda x: x['name'])
        )

        DataFile.objects.create(
            dataset=dataset, filename='filename3',
            size=0, algorithm='md5', checksum='bogus',
            directory='subdir2')
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        # 'filename3' is not in the dir_path we are querying,
        # so it shouldn't appear in the results:
        expected_data = [
            {
                'name': 'filename1'

            },
            {
                'name': 'filename2'
            }
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x['name']),
            sorted(expected_data, key=lambda x: x['name'])
        )

        DataFile.objects.create(
            dataset=dataset, filename='filename4',
            size=0, algorithm='md5', checksum='bogus',
            directory='subdir/subdir3')
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        expected_data = [
            {
                'name': 'filename1'

            },
            {
                'name': 'filename2'
            },
            {
                'name': 'subdir3',
                'path': 'subdir/subdir3',
                'children': []
            }
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x['name']),
            sorted(expected_data, key=lambda x: x['name'])
        )

        uri = '/api/v1/dataset/%d/child-dir-nodes/?dir_path=subdir/subdir3' % dataset.id
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        expected_data = [
            {
                'name': 'filename4'

            },
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x['name']),
            sorted(expected_data, key=lambda x: x['name'])
        )

        dataset.delete()

    def test_get_child_dir_nodes_no_files_in_root_dir(self):
        dataset = Dataset.objects.create(description='test dataset')
        encoded_subdir1 = quote("subdir#1")
        uri = '/api/v1/dataset/%d/child-dir-nodes/?dir_path=%s' % (dataset.id, encoded_subdir1)

        DataFile.objects.create(
            dataset=dataset, filename='filename1',
            size=0, algorithm='md5', checksum='bogus',
            directory='subdir#1')
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data, [
            {
                'name': 'filename1'
            }
        ])

        DataFile.objects.create(
            dataset=dataset, filename='filename2',
            size=0, algorithm='md5', checksum='bogus',
            directory='subdir#1/subdir#2')
        uri = '/api/v1/dataset/%d/child-dir-nodes/?dir_path=%s' % (dataset.id, encoded_subdir1)
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        expected_data = [
            {
                'name': 'filename1',
            },
            {
                'name': 'subdir#2',
                'path': 'subdir#1/subdir#2',
                'children': []
            }
        ]
        self.assertEqual(
            sorted(returned_data, key=lambda x: x['name']),
            sorted(expected_data, key=lambda x: x['name']))
