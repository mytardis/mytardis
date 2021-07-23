from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.dataset import Dataset


class ModelsTestCase(TestCase):
    def __init__(self):
        user = "testuser"
        pwd = User.objects.make_random_password()
        self.user = User.objects.create(
            username=user,
            email="testuser@example.test",
            first_name="Test",
            last_name="User",
        )
        self.user.set_password(pwd)
        self.user.save()
        self.experiment = Experiment.objects.create(
            title="Test Experiment",
            created_by=user,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        self.experiment.save()
        self.dataset1 = Dataset(description="test dataset1")
        self.dataset1.save()
        self.dataset1.experiments.add(experiment)
        self.dataset1.save()
        self.dataset2 = Dataset(description="test dataset2")
        self.dataset2.save()
        self.dataset2.experiments.add(experiment)
        self.dataset2.save()

    def test_dataset_has_pid(self):
        self.assertTrue(hasattr(self.dataset1, "pid"))

    def test_adding_value_to_pid(self):
        pid = "my_test_pid"
        self.dataset1(pid=pid)
        self.dataset1.save()
        self.assertTrue(dataset1.pid == pid)
        self.dataset1(pid=None)
        self.dataset1.save()

    def test_duplicate_pids_raises_error(self):
        pid = "my_test_pid"
        self.dataset1(pid=pid)
        self.dataset1.save()
        self.dataset2(pid=pid)
        with self.assertRaises(IntegrityError):
            self.dataset2.save()
