# -*- coding: utf-8 -*-
"""
test_dataset.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
from django.contrib.auth.models import Group

from tardis.tardis_portal.models import (
    Dataset,
    DataFile,
    Experiment,
    ExperimentACL,
    Facility,
    Instrument,
)

from . import ModelTestCase


class DatasetTestCase(ModelTestCase):
    def test_dataset(self):
        exp = Experiment(
            title="test exp1", institution_name="monash", created_by=self.user
        )

        exp.save()
        exp2 = Experiment(
            title="test exp2", institution_name="monash", created_by=self.user
        )
        exp2.save()

        group = Group(name="Test Manager Group")
        group.save()
        group.user_set.add(self.user)
        facility = Facility(name="Test Facility", manager_group=group)
        facility.save()
        instrument = Instrument(name="Test Instrument", facility=facility)
        instrument.save()

        dataset = Dataset(description="test dataset1")
        dataset.instrument = instrument
        dataset.save()
        dataset.experiments.set([exp, exp2])
        dataset.save()
        dataset_id = dataset.id

        del dataset
        dataset = Dataset.objects.get(pk=dataset_id)

        self.assertEqual(dataset.description, "test dataset1")
        self.assertEqual(dataset.experiments.count(), 2)
        self.assertIn(exp, list(dataset.experiments.iterator()))
        self.assertIn(exp2, list(dataset.experiments.iterator()))
        self.assertEqual(instrument, dataset.instrument)
        target_id = Dataset.objects.first().id
        self.assertEqual(
            dataset.get_absolute_url(),
            "/dataset/view/%d/" % target_id,
            dataset.get_absolute_url() + " != /dataset/view/%d/" % target_id,
        )

    def test_get_dir_tuples(self):

        exp = Experiment(
            title="test exp1", institution_name="monash", created_by=self.user
        )
        exp.save()
        acl = ExperimentACL(
            experiment=exp,
            user=self.user,
            canRead=True,
            canDownload=True,
            canWrite=True,
            canDelete=True,
            canSensitive=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()

        dataset = Dataset.objects.create(description="test dataset1")
        dataset.experiments.add(exp)

        basedir = ""
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [])
        self.assertEqual(dataset.get_dir_nodes(dir_tuples), [])

        DataFile.objects.create(
            dataset=dataset, filename="filename1", size=0, md5sum="bogus"
        )
        basedir = ""
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [])
        self.assertEqual(dataset.get_dir_nodes(dir_tuples), [])

        DataFile.objects.create(
            dataset=dataset,
            filename="filename2",
            size=0,
            md5sum="bogus",
            directory=None,
        )
        basedir = ""
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [])
        self.assertEqual(dataset.get_dir_nodes(dir_tuples), [])

        DataFile.objects.create(
            dataset=dataset, filename="filename3", size=0, md5sum="bogus", directory=""
        )
        basedir = ""
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [])
        self.assertEqual(dataset.get_dir_nodes(dir_tuples), [])

        DataFile.objects.create(
            dataset=dataset,
            filename="filename4",
            size=0,
            md5sum="bogus",
            directory="dir1",
        )
        basedir = ""
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [("dir1", "dir1")])
        self.assertEqual(
            dataset.get_dir_nodes(dir_tuples),
            [{"name": "dir1", "path": "dir1", "children": []}],
        )

        DataFile.objects.create(
            dataset=dataset,
            filename="filename5",
            size=0,
            md5sum="bogus",
            directory="dir1/subdir1",
        )
        basedir = "dir1"
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [("..", "dir1"), ("subdir1", "dir1/subdir1")])
        self.assertEqual(
            dataset.get_dir_nodes(dir_tuples),
            [{"name": "subdir1", "path": "dir1/subdir1", "children": []}],
        )
        basedir = "dir1/subdir1"
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [("..", "dir1/subdir1")])
        self.assertEqual(dataset.get_dir_nodes(dir_tuples), [])

        DataFile.objects.create(
            dataset=dataset,
            filename="filename6",
            size=0,
            md5sum="bogus",
            directory="dir2/subdir2",
        )
        basedir = ""
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [("dir1", "dir1"), ("dir2", "dir2")])
        self.assertEqual(
            dataset.get_dir_nodes(dir_tuples),
            [
                {"name": "dir1", "path": "dir1", "children": []},
                {"name": "dir2", "path": "dir2", "children": []},
            ],
        )
        self.assertEqual(
            dataset.get_dir_tuples(self.user, "dir2"),
            [("..", "dir2"), ("subdir2", "dir2/subdir2")],
        )
        self.assertEqual(
            dataset.get_dir_tuples(self.user, "dir2/subdir2"), [("..", "dir2/subdir2")]
        )
