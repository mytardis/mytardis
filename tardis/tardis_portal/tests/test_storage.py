"""
test_storage.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Grischa Meyer <grischa@gmail.com>

"""
import six

from django.test import TestCase

from ..models import StorageBox, StorageBoxOption
from ..models import Dataset
from ..models import DataFile


class ModelTestCase(TestCase):

    def setUp(self):
        self.test_box = StorageBox(name='test box',
                                   status='online',
                                   max_size=123)
        self.test_box.save()

    def test_storageboxoption(self):
        string_input = 'some credential'
        object_input = {'a dictionary': 'of different things',
                        'booleans': True,
                        'and nothing': None}
        string_option = StorageBoxOption(storage_box=self.test_box,
                                         key='an_option',
                                         value=string_input)
        string_option.save()

        if six.PY2:
            # Storing Pickle data in a TextField can't be done in
            # Python 3, as Django will call force_text which will
            # try to decode the data as UTF-8.
            object_option = StorageBoxOption(storage_box=self.test_box,
                                             key='optional',
                                             value_type=StorageBoxOption.PICKLE)
            object_option.unpickled_value = object_input
            object_option.save()

        options_dict = self.test_box.get_options_as_dict()
        self.assertEqual(options_dict['an_option'], string_input)
        if six.PY2:
            self.assertEqual(options_dict['optional'], object_input)

    def test_get_receiving_box(self):
        dataset = Dataset(description="dataset description")
        dataset.save()

        df_file = DataFile(
            dataset=dataset, filename='file.txt', size=42, md5sum='bogus')
        df_file.save()

        receiving_box = df_file.get_receiving_storage_box()
        self.assertEqual(
            receiving_box.attributes.get(key='type').value, 'receiving')

    def tearDown(self):
        self.test_box.delete()
