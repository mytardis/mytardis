import hashlib
from os import path, urandom

from compare import expect
from django.core.files.base import ContentFile
from django.test import TestCase
from tempfile import NamedTemporaryFile

from tardis.tardis_portal.models import Experiment, Dataset, DataFile, \
    User, UserProfile, DataFileObject, StorageBox

from tardis.tardis_portal.tasks import verify_dfos


class BackgroundTaskTestCase(TestCase):
    """ As per: http://library.stanford.edu/iiif/image-api/compliance.html """

    def setUp(self):
        self.dataset = self._create_dataset()

    def _create_dataset(self):
        user = User.objects.create_user('testuser', 'user@email.test', 'pwd')
        user.save()
        UserProfile(user=user).save()
        full_access = Experiment.PUBLIC_ACCESS_FULL
        experiment = Experiment.objects.create(title="Background Test",
                                               created_by=user,
                                               public_access=full_access)
        experiment.save()
        dataset = Dataset()
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()
        return dataset

    def testLocalFile(self):
        content = urandom(1024)
        cf = ContentFile(content, 'background_task_testfile')

        # Create new Datafile
        datafile = DataFile(dataset=self.dataset)
        datafile.filename = cf.name
        datafile.size = len(content)
        datafile.sha512sum = hashlib.sha512(content).hexdigest()
        datafile.save()
        datafile.file_object = cf

        dfo = datafile.file_objects.all()[0]
        # undo auto-verify:
        dfo.verified = False
        dfo.save(update_fields=['verified'])

        # Check that it's not currently verified
        expect(datafile.verified).to_be(False)
        # Check it verifies
        verify_dfos()
        expect(datafile.verified).to_be(True)

    def test_wrong_size_verification(self):
        content = urandom(1024)
        cf = ContentFile(content, 'background_task_testfile')

        # Create new Datafile
        datafile = DataFile(dataset=self.dataset)
        datafile.filename = cf.name
        datafile.size = len(content) - 1
        datafile.sha512sum = hashlib.sha512(content).hexdigest()
        datafile.save()
        datafile.file_object = cf
        # verify explicitly to catch Exceptions hidden by celery
        datafile.verify()
        self.assertFalse(datafile.file_objects.get().verified)
