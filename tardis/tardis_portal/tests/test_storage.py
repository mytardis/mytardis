"""
test_storage.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Grischa Meyer <grischa@gmail.com>

"""
from django.test import TestCase
from tardis.tardis_portal.models import StorageBox, StorageBoxOption


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
        object_option = StorageBoxOption(storage_box=self.test_box,
                                         key='optional',
                                         value_type=StorageBoxOption.PICKLE)
        object_option.unpickled_value = object_input
        object_option.save()

        options_dict = self.test_box.get_options_as_dict()
        self.assertEqual(options_dict['an_option'], string_input)
        self.assertEqual(options_dict['optional'], object_input)

    def tearDown(self):
        self.test_box.delete()
