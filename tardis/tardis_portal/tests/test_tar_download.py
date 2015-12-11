import hashlib
import os
from StringIO import StringIO
from tarfile import TarFile
from tempfile import NamedTemporaryFile

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from tardis.tardis_portal.models import Experiment


class TarDownloadTestCase(TestCase):

    def setUp(self):
        # create user
        self.testuser = User(username='testuser')
        self.testuser.save()

        # create test experiment
        self.exp = Experiment(title='tar download test' * 15,
                              created_by=self.testuser,
                              public_access=Experiment.PUBLIC_ACCESS_FULL)
        self.exp.save()

        # create test dataset
        self.ds = self.exp.datasets.create(
            description="testing tar download dataset")

        datafile_content = "\n".join(['some data %d' % i
                                      for i in range(1000)])
        filesize = len(datafile_content)
        md5sum = hashlib.md5(datafile_content).hexdigest()
        # create test datafiles and datafile objects
        self.dfs = []
        for i in range(20):
            df = self.ds.datafile_set.create(
                filename='testfile%d.txt' % i,
                mimetype='text/plain',
                size=filesize,
                md5sum=md5sum,
                directory='/'.join([
                    'testdir%d' % i
                    for i in range(i, i + 4)
                ]))
            df.file_object = StringIO(datafile_content)
            df.refresh_from_db()
            self.dfs.append(df)

        # mock client
        self.client = Client()

    def tearDown(self):
        # delete created objects and files

        [ds.delete() for ds in self.exp.datasets.all()]
        self.exp.delete()

    def test_tar_experiment_download(self):
        self.assertTrue(all(df.verified for df in self.dfs))
        response = self.client.get(reverse(
            'tardis.tardis_portal.download.streaming_download_experiment',
            args=(self.exp.id, 'tar')))
        with NamedTemporaryFile('w') as tarfile:
            for c in response.streaming_content:
                tarfile.write(c)
            tarfile.flush()
            self.assertEqual(int(response['Content-Length']),
                             os.stat(tarfile.name).st_size)
            tf = TarFile(tarfile.name)
            for df in self.dfs:
                full_path = os.path.join(
                    self.exp.title.replace(' ', '_'), self.ds.description,
                    df.directory, df.filename)
                tf.extract(full_path, '/tmp')
                self.assertEqual(
                    os.stat(os.path.join('/tmp', full_path)).st_size,
                    int(df.size))
