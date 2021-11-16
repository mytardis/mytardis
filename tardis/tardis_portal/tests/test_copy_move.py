# -*- coding: utf-8 -*-
"""
test_copy_move.py

Test copying and moving a file to another storage box

.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
import hashlib
import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from ..models.dataset import Dataset
from ..models.datafile import DataFile, DataFileObject
from ..models.storage import StorageBox, StorageBoxAttribute


class CopyMoveTestCase(TestCase):
    """
    Test copying and moving files between storage boxes
    """

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username='PUBLIC_USER_TEST')
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.dataset = Dataset.objects.create(description="test-dataset")
        file_content = u'bla'
        md5sum = hashlib.md5(file_content.encode('utf-8')).hexdigest()
        self.datafile = DataFile.objects.create(
            dataset=self.dataset, filename="file.txt", size=3, md5sum=md5sum)
        self.default_storage_box = StorageBox.get_default_storage()
        with tempfile.NamedTemporaryFile() as temp:
            second_location = temp.name
        if not os.path.exists(second_location):
            os.makedirs(second_location)
        self.second_box = StorageBox.create_local_box(location=second_location)
        self.dfo = DataFileObject.objects.create(
            datafile=self.datafile, storage_box=self.default_storage_box,
            uri = "test-dataset-%s/file.txt" % self.dataset.id)
        dataset_dir = os.path.dirname(self.dfo.get_full_path())
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
        with open(self.dfo.get_full_path(), 'w') as file_obj:
            file_obj.write(u'bla')

    def tearDown(self):
        self.dataset.delete()
        shutil.rmtree(self.second_box.options.get(key='location').value)
        self.second_box.delete()

    def test_copy(self):
        """
        Test copying a file to another storage box
        """
        # Attempting to copy and unverified file should fail and return False:
        self.assertFalse(self.dfo.verified)
        self.assertFalse(self.dfo.copy_file(self.second_box))

        # Now verify the file and test copying it to self.second_box:
        self.assertTrue(self.dfo.verify())
        self.assertTrue(self.dfo.copy_file(self.second_box))
        copy = DataFileObject.objects.filter(
            datafile=self.datafile, storage_box=self.second_box).first()
        self.assertIsNotNone(copy)
        self.assertEqual(copy.storage_box.id, self.second_box.id)
        self.assertTrue(copy.verify())
        self.assertEqual(
            DataFileObject.objects.filter(datafile=self.datafile).count(), 2)

        # Now let's make the second storage box's copy unverified, and check
        # whether copy_file triggers its verification:
        copy.verified = False
        copy.save()
        copy = self.dfo.copy_file(self.second_box)
        # Thanks to CELERY_ALWAYS_EAGER = True in test_settings.py:
        self.assertTrue(copy.verified)

        # Now let's delete the copy in self.second_box:
        copy.delete()
        self.assertEqual(
            DataFileObject.objects.filter(datafile=self.datafile).count(), 1)

        # Now let's make the second storage box invalid by removing its
        # location StorageBoxOption and then try copying to it again
        # which should fail, returning False:
        self.second_box.django_storage_class = "invalid"
        self.second_box.save()
        self.assertFalse(self.dfo.copy_file(self.second_box))

    def test_move(self):
        """
        Test moving a file to another storage box
        """
        self.assertTrue(self.dfo.verify())
        self.assertTrue(self.dfo.move_file(self.second_box))
        copy = DataFileObject.objects.filter(
            datafile=self.datafile, storage_box=self.second_box).first()
        self.assertIsNotNone(copy)
        self.assertEqual(copy.storage_box.id, self.second_box.id)
        self.assertTrue(copy.verify())
        self.assertEqual(
            DataFileObject.objects.filter(datafile=self.datafile).count(), 1)

    def test_cache(self):
        """
        Test caching a file from a slow-access storage box
        """
        tape_attr = StorageBoxAttribute.objects.create(
            storage_box=self.default_storage_box, key='type', value='tape')
        self.default_storage_box.attributes.add(tape_attr)
        cache_attr = StorageBoxAttribute.objects.create(
            storage_box=self.default_storage_box, key='type', value='cache')
        self.second_box.attributes.add(cache_attr)
        self.second_box.master_box = self.default_storage_box
        self.second_box.save()
        self.assertTrue(self.dfo.verify())
        copy = self.dfo.cache_file()
        self.assertEqual(copy.storage_box.id, self.second_box.id)
        copy.delete()

        self.assertFalse(self.datafile.is_online)
        self.datafile.cache_file()
        # Clear cache for is_online @cached_property by creating new instance:
        self.datafile = DataFile.objects.get(id=self.datafile.id)
        self.assertTrue(self.datafile.is_online)
