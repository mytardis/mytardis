from django.test import TestCase
from django.contrib.auth.models import User
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.dataset import Dataset


class ModelsTestCase(TestCase):
    def test_dataset_has_pid(self):
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
        dataset = Dataset(description="test dataset")
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()
        self.assertTrue(hasattr(dataset, "pid"))
