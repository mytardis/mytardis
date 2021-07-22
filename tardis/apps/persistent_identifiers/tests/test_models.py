from django.test import TestCase
from ..models import ExperimentPID
from tardis.tardis_portal.models.experiment import Experiment

class ModelsTestCase(TestCase):
    
    def test_experiment_had_pid(self):
        user = 'testuser'
        pwd = User.objects.make_random_password()
        user = User.objects.create(username=user,
                                        email='testuser@example.test',
                                        first_name="Test", last_name="User")
        user.set_password(pwd)
        user.save()
        experiment = Experiment.objects.create(title="Test Experiment",
                                                    created_by=user,
                                                    public_access=Experiment.PUBLIC_ACCESS_FULL)
        experiment.save()
        self.assertTrue(
            hasattr(experiment,
                    'pid')
            )
