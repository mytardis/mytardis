from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from tardis.tardis_portal.models.experiment import Experiment


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
        self.assertTrue(hasattr(experiment, "pid"))

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
        pid = "my_test_pid"
        experiment.pid.pid = pid
        experiment.pid.save()
        key = experiment.id
        experiment = Experiment.objects.get(pk=key)
        self.assertTrue(experiment.pid.pid == pid)

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
        experiment1 = Experiment.objects.create(
            title="Test Experiment",
            created_by=user,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        experiment1.save()
        experiment2 = Experiment.objects.create(
            title="Test Experiment",
            created_by=user,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        experiment2.save()
        pid = "my_test_pid_2"
        experiment1.pid.pid = pid
        experiment1.pid.save()
        with self.assertRaises(IntegrityError):
            experiment2.pid.pid = pid
            experiment2.pid.save()
