import hashlib
from os import urandom

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import TestCase

from ..models import DataFile, Dataset, Experiment, User
from ..tasks import verify_dfos


class BackgroundTaskTestCase(TestCase):
    """As per: http://library.stanford.edu/iiif/image-api/compliance.html"""

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.dataset = self._create_dataset()

    def _create_dataset(self):
        user = User.objects.create_user("testuser", "user@email.test", "pwd")
        user.save()
        full_access = Experiment.PUBLIC_ACCESS_FULL
        experiment = Experiment.objects.create(
            title="Background Test", created_by=user, public_access=full_access
        )
        experiment.save()
        dataset = Dataset()
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()
        return dataset

    def testLocalFile(self):
        content = urandom(1024)
        cf = ContentFile(content, "background_task_testfile")

        # Create new Datafile
        datafile = DataFile(dataset=self.dataset)
        datafile.filename = cf.name
        datafile.size = len(content)
        datafile.md5sum = hashlib.md5(content).hexdigest()
        datafile.save()
        datafile.file_object = cf

        dfo = datafile.file_objects.all()[0]
        # undo auto-verify:
        dfo.verified = False
        dfo.save(update_fields=["verified"])

        # Check that it's not currently verified
        self.assertFalse(datafile.verified)
        # Check it verifies
        verify_dfos()
        self.assertTrue(datafile.verified)

    def test_wrong_size_verification(self):
        content = urandom(1024)
        cf = ContentFile(content, "background_task_testfile")

        # Create new Datafile
        datafile = DataFile(dataset=self.dataset)
        datafile.filename = cf.name
        datafile.size = len(content) - 1
        datafile.md5sum = hashlib.md5(content).hexdigest()
        datafile.save()
        datafile.file_object = cf
        # verify explicitly to catch Exceptions hidden by celery
        datafile.verify()
        self.assertFalse(datafile.file_objects.get().verified)
