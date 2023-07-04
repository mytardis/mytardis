from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

# from tardis.apps.projects.models import Project
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment

# from tardis.tardis_portal.models.facility import Facility
# from tardis.tardis_portal.models.instrument import Instrument


class ModelsTestCase(TestCase):
    def test_model_has_pid(self):
        user = "testuser"
        pwd = User.objects.make_random_password()
        user = User.objects.create(
            username=user,
            email="testuser@example.test",
            first_name="Test",
            last_name="User",
        )
        user.set_password(pwd)
        user.save()
        experiment = Experiment.objects.create(
            title="Test Experiment",
            created_by=user,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        experiment.save()
        dataset1 = Dataset(description="test dataset1")
        dataset1.save()
        dataset1.experiments.add(experiment)
        dataset1.save()
        self.assertTrue(hasattr(dataset1, "persistent_id"))

    def test_adding_value_to_pid(self):
        user = "testuser"
        pwd = User.objects.make_random_password()
        user = User.objects.create(
            username=user,
            email="testuser@example.test",
            first_name="Test",
            last_name="User",
        )
        user.set_password(pwd)
        user.save()
        experiment = Experiment.objects.create(
            title="Test Experiment",
            created_by=user,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        experiment.save()
        dataset = Dataset(description="test dataset1")
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()
        pid = "my_test_pid"
        dataset.persistent_id.persistent_id = pid
        dataset.persistent_id.save()
        key = dataset.id
        dataset = Dataset.objects.get(pk=key)
        print(dataset.persistent_id)
        self.assertTrue(dataset.persistent_id.persistent_id == pid)

    def test_duplicate_pids_raises_error(self):
        user = "testuser"
        pwd = User.objects.make_random_password()
        user = User.objects.create(
            username=user,
            email="testuser@example.test",
            first_name="Test",
            last_name="User",
        )
        user.set_password(pwd)
        user.save()
        experiment = Experiment.objects.create(
            title="Test Experiment",
            created_by=user,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        experiment.save()
        dataset1 = Dataset(description="test dataset1")
        dataset1.save()
        dataset1.experiments.add(experiment)
        dataset1.save()
        dataset2 = Dataset(description="test dataset2")
        dataset2.save()
        dataset2.experiments.add(experiment)
        dataset2.save()
        pid = "my_test_pid_2"
        dataset1.persistent_id.persistent_id = pid
        dataset1.persistent_id.save()
        with self.assertRaises(IntegrityError):
            dataset2.persistent_id.persistent_id = pid
            dataset2.persistent_id.save()

    def test_adding_value_to_alternate_idenfiers(self):
        user = "testuser"
        pwd = User.objects.make_random_password()
        user = User.objects.create(
            username=user,
            email="testuser@example.test",
            first_name="Test",
            last_name="User",
        )
        user.set_password(pwd)
        user.save()
        experiment = Experiment.objects.create(
            title="Test Experiment",
            created_by=user,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        experiment.save()
        dataset = Dataset(description="test dataset1")
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()
        alternate_ids = ["my_test_pid1", "my_test_pid2", "my_test_pid3"]
        dataset.persistent_id.alternate_ids = alternate_ids
        dataset.persistent_id.save()
        key = dataset.id
        dataset = Dataset.objects.get(pk=key)
        print(dataset.persistent_id)
        self.assertTrue(dataset.persistent_id.alternate_ids == alternate_ids)
