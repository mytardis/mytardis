'''
Testing the Dataset resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''

import json

from six.moves import urllib

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
            % urllib.parse.quote(self.ds_no_instrument.description)
        output = self.api_client.get(uri,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        self.assertTrue('description' in returned_object)
        self.assertEqual(returned_object['description'],
                         self.ds_no_instrument.description)
        self.assertTrue('instrument' in returned_object)
        self.assertIsNone(returned_object['instrument'])

    def test_get_dataset_with_instrument(self):
        uri = '/api/v1/dataset/?description=%s' \
            % urllib.parse.quote(self.ds_with_instrument.description)
        output = self.api_client.get(uri,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
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
        returned_data = json.loads(output.content)
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
        self.assertHttpCreated(self.api_client.post(
            '/api/v1/dataset/',
            data=post_data,
            authentication=self.get_credentials()))
        self.assertEqual(dataset_count + 1, Dataset.objects.count())

    def test_get_dataset_files(self):
        ds_id = self.ds_no_instrument.id
        uri = '/api/v1/dataset/%d/files/' % ds_id
        response = self.api_client.get(
            uri, authentication=self.get_credentials())
        returned_data = json.loads(response.content)
        self.assertEqual(returned_data['meta']['total_count'], 0)
