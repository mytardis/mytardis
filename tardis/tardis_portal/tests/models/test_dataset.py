# -*- coding: utf-8 -*-
"""
test_dataset.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
from django.conf import settings
from django.contrib.auth.models import Group

from tardis.tardis_portal.models import (
    DataFile,
    DatafileACL,
    Dataset,
    DatasetACL,
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
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.set_acl = DatasetACL(
                user=self.user,
                dataset=dataset,
                isOwner=True,
                canRead=True,
                aclOwnershipType=DatasetACL.OWNER_OWNED,
            )
            self.set_acl.save()
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
            "/dataset/%d" % target_id,
            dataset.get_absolute_url() + " != /dataset/%d" % target_id,
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

        df1 = DataFile.objects.create(
            dataset=dataset, filename="filename1", size=0, md5sum="bogus"
        )
        basedir = ""
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl = DatafileACL(
                user=self.user,
                datafile=df1,
                isOwner=True,
                canRead=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            self.file_acl.save()
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [])
        self.assertEqual(dataset.get_dir_nodes(dir_tuples), [])

        df2 = DataFile.objects.create(
            dataset=dataset,
            filename="filename2",
            size=0,
            md5sum="bogus",
            directory=None,
        )
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl = DatafileACL(
                user=self.user,
                datafile=df2,
                isOwner=True,
                canRead=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            self.file_acl.save()
        basedir = ""
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [])
        self.assertEqual(dataset.get_dir_nodes(dir_tuples), [])

        df3 = DataFile.objects.create(
            dataset=dataset, filename="filename3", size=0, md5sum="bogus", directory=""
        )
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl = DatafileACL(
                user=self.user,
                datafile=df3,
                isOwner=True,
                canRead=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            self.file_acl.save()
        basedir = ""
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [])
        self.assertEqual(dataset.get_dir_nodes(dir_tuples), [])

        df4 = DataFile.objects.create(
            dataset=dataset,
            filename="filename4",
            size=0,
            md5sum="bogus",
            directory="dir1",
        )
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl = DatafileACL(
                user=self.user,
                datafile=df4,
                isOwner=True,
                canRead=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            self.file_acl.save()
        basedir = ""
        dir_tuples = dataset.get_dir_tuples(self.user, basedir)
        self.assertEqual(dir_tuples, [("dir1", "dir1")])
        self.assertEqual(
            dataset.get_dir_nodes(dir_tuples),
            [{"name": "dir1", "path": "dir1", "children": []}],
        )

        df5 = DataFile.objects.create(
            dataset=dataset,
            filename="filename5",
            size=0,
            md5sum="bogus",
            directory="dir1/subdir1",
        )
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl = DatafileACL(
                user=self.user,
                datafile=df5,
                isOwner=True,
                canRead=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            self.file_acl.save()
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

        df6 = DataFile.objects.create(
            dataset=dataset,
            filename="filename6",
            size=0,
            md5sum="bogus",
            directory="dir2/subdir2",
        )
        if not settings.ONLY_EXPERIMENT_ACLS:
            self.file_acl = DatafileACL(
                user=self.user,
                datafile=df6,
                isOwner=True,
                canRead=True,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            self.file_acl.save()
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
