# -*- coding: utf-8 -*-

from compare import expect
from os import makedirs
from os.path import abspath, basename, dirname, join, exists
from shutil import rmtree
from tempfile import mkstemp
from zipfile import is_zipfile, ZipFile

from django.test import TestCase
from django.test.client import Client

from django.conf import settings
from django.contrib.auth.models import User

from nose.plugins.skip import SkipTest

import filecmp

from tardis.tardis_portal.download import StreamingFile
from tardis.tardis_portal.models import Experiment, Dataset, Dataset_File

from tempfile import NamedTemporaryFile

try:
    from wand.image import Image
    IMAGEMAGICK_AVAILABLE = True
except (AttributeError, ImportError):
    IMAGEMAGICK_AVAILABLE = False


def get_size_and_sha512sum(testfile):
    import hashlib
    with open(testfile, 'rb') as f:
        contents = f.read()
        return (len(contents), hashlib.sha512(contents).hexdigest())

class StreamingFileTestCase(TestCase):

    def testDirectCopy(self):

        def writeTestData(filename):
            with open(filename, 'w') as f:
                from time import sleep
                for i in range(1,10):
                    print i
                    sleep(0.1)
                    f.write("%d\n" % i)

        # Create
        reader = StreamingFile(writeTestData, asynchronous_file_creation=True)
        expect(reader.thread.is_alive()).to_be_truthy()
        expect(exists(reader.name)).to_be_truthy()
        contents = reader.read(10)
        expect(contents).to_equal("\n".join(map(str,range(1,6)))+"\n")
        contents = reader.read(1024)
        expect(contents).to_equal("\n".join(map(str,range(6,10)))+"\n")
        contents = reader.read(1024)
        expect(contents).to_equal('')
        expect(exists(reader.name)).to_be_truthy()
        reader.close()
        expect(exists(reader.name)).to_be_falsy()



class DownloadTestCase(TestCase):

    def setUp(self):
        # create a test user
        self.user = User.objects.create_user(username='DownloadTestUser',
                                             email='',
                                             password='secret')

        # create a public experiment
        self.experiment1 = Experiment(title='Experiment 1',
                                      created_by=self.user,
                                      public_access=Experiment.PUBLIC_ACCESS_FULL)
        self.experiment1.save()

        # create a non-public experiment
        self.experiment2 = Experiment(title='Experiment 2',
                                      created_by=self.user,
                                      public_access=Experiment.PUBLIC_ACCESS_NONE)
        self.experiment2.save()

        # dataset1 belongs to experiment1
        self.dataset1 = Dataset()
        self.dataset1.save()
        self.dataset1.experiments.add(self.experiment1)
        self.dataset1.save()


        # dataset2 belongs to experiment2
        self.dataset2 = Dataset()
        self.dataset2.save()
        self.dataset2.experiments.add(self.experiment2)
        self.dataset2.save()

        # absolute path first
        filename1 = 'testfile.txt'
        filename2 = 'testfile.tiff'
        self.dest1 = abspath(join(settings.FILE_STORE_PATH, '%s/%s/'
                                  % (self.experiment1.id,
                                  self.dataset1.id)))
        self.dest2 = abspath(join(settings.FILE_STORE_PATH,
                                '%s/%s/'
                                  % (self.experiment2.id,
                                  self.dataset2.id)))
        if not exists(self.dest1):
            makedirs(self.dest1)
        if not exists(self.dest2):
            makedirs(self.dest2)

        testfile1 = abspath(join(self.dest1, filename1))
        f = open(testfile1, 'w')
        f.write("Hello World!\n")
        f.close()

        testfile2 = abspath(join(self.dest2, filename2))
        if IMAGEMAGICK_AVAILABLE:
            with Image(filename='logo:') as img:
                img.format = 'tiff'
                img.save(filename=testfile2)
        else:
            # Apparently ImageMagick isn't installed...
            # Write a "fake" TIFF file
            f = open(testfile2, 'w')
            f.write("II\x2a\x00")
            f.close()


        size, sha512sum = get_size_and_sha512sum(testfile1)
        self.dataset_file1 = Dataset_File(dataset=self.dataset1,
                                          filename=filename1,
                                          protocol='',
                                          size=size,
                                          sha512sum=sha512sum,
                                          url='%d/%d/%s'
                                              % (self.experiment1.id,
                                                 self.dataset1.id,
                                                 filename1))
        self.dataset_file1.verify()
        self.dataset_file1.save()

        size, sha512sum = get_size_and_sha512sum(testfile2)
        self.dataset_file2 = Dataset_File(dataset=self.dataset2,
                                          filename=basename(filename2),
                                          protocol='',
                                          size=size,
                                          sha512sum=sha512sum,
                                          url='%d/%d/%s'
                                            % (self.experiment2.id,
                                               self.dataset2.id,
                                               filename2))
        self.dataset_file2.verify()
        self.dataset_file2.save()

    def tearDown(self):
        self.user.delete()
        self.experiment1.delete()
        self.experiment2.delete()
        rmtree(self.dest1)
        rmtree(self.dest2)

    def testView(self):
        client = Client()

        # check view of file1
        response = client.get('/datafile/view/%i/' % self.dataset_file1.id)

        self.assertEqual(response['Content-Disposition'],
                         'inline; filename="%s"'
                         % self.dataset_file1.filename)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Hello World!\n')

        # check view of file2
        response = client.get('/datafile/view/%i/' % self.dataset_file2.id)
        # Should be forbidden
        self.assertEqual(response.status_code, 403)

        self.experiment2.public_access=Experiment.PUBLIC_ACCESS_FULL
        self.experiment2.save()
        # check view of file2 again
        response = client.get('/datafile/view/%i/' % self.dataset_file2.id)
        self.assertEqual(response.status_code, 200)

        # The following behaviour relies on ImageMagick
        if IMAGEMAGICK_AVAILABLE:
            # file2 should have a ".png" filename
            self.assertEqual(response['Content-Disposition'],
                             'inline; filename="%s"'
                             % (self.dataset_file2.filename+'.png'))
            # file2 should be a PNG
            self.assertEqual(response['Content-Type'], 'image/png')
            png_signature = "\x89PNG\r\n\x1a\n"
            self.assertEqual(response.content[0:8], png_signature)
        else:
            # file2 should have a ".tiff" filename
            self.assertEqual(response['Content-Disposition'],
                             'inline; filename="%s"'
                             % (self.dataset_file2.filename))
            # file2 should be a TIFF
            self.assertEqual(response['Content-Type'], 'image/tiff')
            tiff_signature = "II\x2a\x00"
            self.assertEqual(response.content[0:4], tiff_signature)

    def _check_tar_file(self, content, rootdir, datafiles):
        # It should be a zip file
        with NamedTemporaryFile('w') as tempfile:
            tempfile.write(content)
            tempfile.flush()
            with open(tempfile.name, 'r') as zipread:
                # It should be a zip file (all of which start with "PK")
                expect(zipread.read(2)).to_equal('PK')
            expect(is_zipfile(tempfile.name)).to_be_truthy()
            with ZipFile(tempfile.name, 'r') as zf:
                expect(len(zf.namelist())).to_equal(len(datafiles))
                for df in datafiles:
                    filename = join(rootdir, str(df.dataset.id), df.filename)
                    expect(filename in zf.namelist()).to_be_truthy()

    def _check_zip_file(self, content, rootdir, datafiles):
        # It should be a zip file
        with NamedTemporaryFile('w') as tempfile:
            tempfile.write(content)
            tempfile.flush()
            with open(tempfile.name, 'r') as zipread:
                # It should be a zip file (all of which start with "PK")
                expect(zipread.read(2)).to_equal('PK')
            expect(is_zipfile(tempfile.name)).to_be_truthy()
            zf = ZipFile(tempfile.name, 'r')
            expect(len(zf.namelist())).to_equal(len(datafiles))
            for df in datafiles:
                filename = join(rootdir, str(df.dataset.id), df.filename)
                expect(filename in zf.namelist()).to_be_truthy()
            zf.close()


    def testDownload(self):
        client = Client()

        # check download for experiment1
        response = client.get('/download/experiment/%i/zip/' % self.experiment1.id)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="experiment%s-complete.zip"'
                         % self.experiment1.id)
        self.assertEqual(response.status_code, 200)
        self._check_zip_file(response.content, str(self.experiment1.id),
                             reduce(lambda x, y: x + y,
                                    [ds.dataset_file_set.all() \
                                     for ds in self.experiment1.datasets.all()]))

        # check download of file1
        response = client.get('/download/datafile/%i/' % self.dataset_file1.id)

        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="%s"'
                         % self.dataset_file1.filename)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Hello World!\n')

        # requesting file2 should be forbidden...
        response = client.get('/download/datafile/%i/' % self.dataset_file2.id)
        self.assertEqual(response.status_code, 403)

        # check dataset1 download
        response = client.post('/download/datafiles/',
                               {'expid': self.experiment1.id,
                                'dataset': [self.dataset1.id],
                                'datafile': []})
        self.assertEqual(response.status_code, 200)
        self._check_zip_file(response.content, 'datasets',
                             self.dataset1.dataset_file_set.all())

        # check dataset2 download
        response = client.post('/download/datafiles/',
                               {'expid': self.experiment2.id,
                                'dataset': [self.dataset2.id],
                                'datafile': []})
        self.assertEqual(response.status_code, 403)

        # check datafile1 download via POST
        response = client.post('/download/datafiles/',
                               {'expid': self.experiment1.id,
                                'dataset': [],
                                'datafile': [self.dataset_file1.id]})
        self.assertEqual(response.status_code, 200)
        self._check_zip_file(response.content, 'datasets', [self.dataset_file1])

        # check datafile2 download via POST
        response = client.post('/download/datafiles/',
                               {'expid': self.experiment2.id,
                                'dataset': [],
                                'datafile': [self.dataset_file2.id]})
        self.assertEqual(response.status_code, 403)

        # Check datafile2 download with second experiment to "metadata only"
        self.experiment2.public_access=Experiment.PUBLIC_ACCESS_METADATA
        self.experiment2.save()
        response = client.get('/download/datafile/%i/' % self.dataset_file2.id)
        # Metadata-only means "no file access"!
        self.assertEqual(response.status_code, 403)

        # Check datafile2 download with second experiment to public
        self.experiment2.public_access=Experiment.PUBLIC_ACCESS_FULL
        self.experiment2.save()
        response = client.get('/download/datafile/%i/' % self.dataset_file2.id)
        self.assertEqual(response.status_code, 200)
        # This should be a TIFF (which often starts with "II\x2a\x00")
        self.assertEqual(response['Content-Type'], 'image/tiff')
        self.assertEqual(response.content[0:4], "II\x2a\x00")


    def testDatasetFile(self):

        # check registered text file for physical file meta information
        df = Dataset_File.objects.get(pk=self.dataset_file1.id)

        try:
            from magic import Magic
            self.assertEqual(df.mimetype, 'text/plain; charset=us-ascii')
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
        self.assertEqual(df.size, str(13))
        self.assertEqual(df.md5sum, '8ddd8be4b179a529afa5f2ffae4b9858')

        # now check a JPG file
        filename = abspath(join(dirname(__file__),
                                '../static/images/ands-logo-hi-res.jpg'))

        dataset = Dataset.objects.get(pk=self.dataset1.id)

        size, sha512sum = get_size_and_sha512sum(filename)
        pdf1 = Dataset_File(dataset=dataset,
                            filename=basename(filename),
                            size=str(size),
                            sha512sum=sha512sum,
                            url='file://%s' % filename,
                            protocol='file')
        pdf1.verify()
        pdf1.save()
        try:
            from magic import Magic
            self.assertEqual(pdf1.mimetype, 'image/jpeg')
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
        self.assertEqual(pdf1.size, str(14232))
        self.assertEqual(pdf1.md5sum, 'c450d5126ffe3d14643815204daf1bfb')

        # now check that we can override the physical file meta information
        pdf2 = Dataset_File(dataset=dataset,
                            filename=basename(filename),
                            url='file://%s' % filename,
                            protocol='file',
                            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                            size=str(0),
                            # Empty string always has the same hash
                            sha512sum='cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e')
        pdf2.save()
        try:
            from magic import Magic
            self.assertEqual(pdf2.mimetype, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
        self.assertEqual(pdf2.size, str(0))
        self.assertEqual(pdf2.md5sum, '')

        pdf2.mimetype = ''
        pdf2.save()

        try:
            from magic import Magic
            self.assertEqual(pdf2.mimetype, 'application/pdf')
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
