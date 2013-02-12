import hashlib
from os import path, urandom

from compare import ensure, expect
from django.core.files.base import ContentFile
from django.test import TestCase
from tempfile import NamedTemporaryFile

from tardis.tardis_portal.models import Experiment, Dataset, Dataset_File, \
    Replica, Location, User, UserProfile
from tardis.tardis_portal.staging import write_uploaded_file_to_dataset

from tardis.tardis_portal.tasks import verify_files

class BackgroundTaskTestCase(TestCase):
    """ As per: http://library.stanford.edu/iiif/image-api/compliance.html """

    def setUp(self):
        Location.force_initialize()
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
        datafile = Dataset_File(dataset=self.dataset)
        datafile.filename = cf.name
        datafile.size = len(content)
        datafile.sha512sum = hashlib.sha512(content).hexdigest()
        datafile.save()
        replica = Replica(datafile=datafile,
                          url=write_uploaded_file_to_dataset(self.dataset, cf),
                          location=Location.get_default_location())
        replica.save()

        def get_replica(datafile):
            return Replica.objects.get(datafile=datafile)

        # Check that it's not currently verified
        expect(get_replica(datafile).verified).to_be(False)

        # Check it verifies
        verify_files()
        expect(get_replica(datafile).verified).to_be(True)


    def testRemoteFile(self):
            content = urandom(1024)
            with NamedTemporaryFile() as f:
                # Create new Datafile
                datafile = Dataset_File(dataset=self.dataset)
                datafile.filename = 'background_task_testfile'
                datafile.size = len(content)
                datafile.sha512sum = hashlib.sha512(content).hexdigest()
                datafile.save()
                replica = Replica(datafile=datafile,
                                  location=Location.get_location('staging'),
                                  url='file://' + path.abspath(f.name))
                replica.save()

                def get_replica(replica):
                    return Replica.objects.get(id=replica.id)

                # Check that it won't verify as it stands
                expect(get_replica(replica).verified).to_be(False)
                verify_files()
                expect(get_replica(replica).verified).to_be(False)
                expect(get_replica(replica).is_local()).to_be(False)

                # Fill in the content
                f.write(content)
                f.flush()

                # Check it now verifies
                verify_files()
                expect(get_replica(replica).verified).to_be(True)
                expect(get_replica(replica).is_local()).to_be(True)
