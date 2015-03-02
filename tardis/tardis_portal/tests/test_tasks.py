import hashlib
from os import path, urandom

from compare import expect
from django.core.files.base import ContentFile
from django.test import TestCase
from tempfile import NamedTemporaryFile

from tardis.tardis_portal.models import Experiment, Dataset, DataFile, \
    User, DataFileObject, StorageBox

from tardis.tardis_portal.tasks import verify_dfos


class BackgroundTaskTestCase(TestCase):
    """ As per: http://library.stanford.edu/iiif/image-api/compliance.html """

    def setUp(self):
        self.dataset = self._create_dataset()

    def _create_dataset(self):
        user = User.objects.create_user('testuser', 'user@email.test', 'pwd')
        user.save()
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

# disabled, because verification doesn't ingest from remote anymore
# need to amend once staging ingestion is set up again
    # def testRemoteFile(self):
    #         content = urandom(1024)
    #         with NamedTemporaryFile() as f:
    #             # Create new Datafile
    #             datafile = DataFile(dataset=self.dataset)
    #             datafile.filename = 'background_task_testfile'
    #             datafile.size = len(content)
    #             datafile.sha512sum = hashlib.sha512(content).hexdigest()
    #             datafile.save()
    #             url = path.abspath(f.name)
    #             base_url = path.dirname(path.abspath(f.name))
    #             datafile.dataset.storage_boxes.add(
    #                 StorageBox.get_default_storage(location=base_url))
    #             dfo = DataFileObject(
    #                 datafile=datafile,
    #                 storage_box=datafile.dataset.storage_boxes.all()[-1],
    #                 uri=url)
    #             dfo.save()

    #             # Check that it won't verify as it stands
    #             expect(datafile.verified).to_be(False)
    #             verify_dfos()
    #             expect(datafile.verified).to_be(False)

    #             # Fill in the content
    #             f.write(content)
    #             f.flush()

    #             # Check it now verifies
    #             verify_dfos()
    #             expect(get_replica).id).to_be(
    #                 get_new_replica(datafile).id)
    #             expect(get_new_replica(datafile).verified).to_be(True)
    #             expect(get_new_replica(datafile).is_local()).to_be(True)
