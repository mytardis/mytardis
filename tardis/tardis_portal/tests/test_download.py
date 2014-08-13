# -*- coding: utf-8 -*-

from compare import expect
from os import makedirs
from os.path import abspath, basename, dirname, join, exists, getsize
from shutil import rmtree
from zipfile import is_zipfile, ZipFile
from tarfile import is_tarfile, TarFile

from django.test import TestCase
from django.test.client import Client

from django.conf import settings
from django.contrib.auth.models import User

from tardis.tardis_portal.models import \
    Experiment, Dataset, DataFile, DataFileObject

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


def _generate_test_image(testfile):
    if IMAGEMAGICK_AVAILABLE:
        with Image(filename='logo:') as img:
            img.format = 'tiff'
            img.save(filename=testfile)
    else:
        # Apparently ImageMagick isn't installed...
        # Write a "fake" TIFF file
        f = open(testfile, 'w')
        f.write("II\x2a\x00")
        f.close()


class DownloadTestCase(TestCase):

    def setUp(self):
        # create a test user
        self.user = User.objects.create_user(username='DownloadTestUser',
                                             email='',
                                             password='secret')

        # create a public experiment
        self.experiment1 = Experiment(
            title='Experiment 1',
            created_by=self.user,
            public_access=Experiment.PUBLIC_ACCESS_FULL)
        self.experiment1.save()

        # create a non-public experiment
        self.experiment2 = Experiment(
            title='Experiment 2',
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
        _generate_test_image(testfile2)

        self.datafile1 = self._build_datafile(
            testfile1, filename1, self.dataset1,
            '%d/%d/%s' % (self.experiment1.id, self.dataset1.id, filename1))

        self.datafile2 = self._build_datafile(
            testfile2, filename2, self.dataset2,
            '%d/%d/%s' % (self.experiment2.id, self.dataset2.id, filename2))

    def _build_datafile(self, testfile, filename, dataset, url,
                        checksum=None, size=None, mimetype=''):
        filesize, sha512sum = get_size_and_sha512sum(testfile)
        datafile = DataFile(dataset=dataset, filename=filename,
                            mimetype=mimetype,
                            size=str(size if size is not None else filesize),
                            sha512sum=(checksum if checksum else sha512sum))
        datafile.save()
        dfo = DataFileObject(
            datafile=datafile,
            storage_box=datafile.dataset.get_default_storage_box(),
            uri=url)
        dfo.save()
        return DataFile.objects.get(pk=datafile.pk)

    def tearDown(self):
        self.user.delete()
        self.experiment1.delete()
        self.experiment2.delete()
        rmtree(self.dest1)
        rmtree(self.dest2)

    def testView(self):
        client = Client()

        # check view of file1
        response = client.get('/datafile/view/%i/' % self.datafile1.id)

        self.assertEqual(response['Content-Disposition'],
                         'inline; filename="%s"'
                         % self.datafile1.filename)
        self.assertEqual(response.status_code, 200)
        response_content = ""
        for c in response.streaming_content:
            response_content += c
        self.assertEqual(response_content, 'Hello World!\n')

        # check view of file2
        response = client.get('/datafile/view/%i/' % self.datafile2.id)
        # Should be forbidden
        self.assertEqual(response.status_code, 403)

        self.experiment2.public_access = Experiment.PUBLIC_ACCESS_FULL
        self.experiment2.save()
        # check view of file2 again
        response = client.get('/datafile/view/%i/' % self.datafile2.id)
        self.assertEqual(response.status_code, 200)

        # The following behaviour relies on ImageMagick
        if IMAGEMAGICK_AVAILABLE:
            # file2 should have a ".png" filename
            self.assertEqual(response['Content-Disposition'],
                             'inline; filename="%s"'
                             % (self.datafile2.filename+'.png'))
            # file2 should be a PNG
            self.assertEqual(response['Content-Type'], 'image/png')
            png_signature = "\x89PNG\r\n\x1a\n"
            self.assertEqual(response.content[0:8], png_signature)
        else:
            # file2 should have a ".tiff" filename
            self.assertEqual(response['Content-Disposition'],
                             'inline; filename="%s"'
                             % (self.datafile2.filename))
            # file2 should be a TIFF
            self.assertEqual(response['Content-Type'], 'image/tiff')
            tiff_signature = "II\x2a\x00"
            self.assertEqual(response.content[0:4], tiff_signature)

    def _check_tar_file(self, content, rootdir, datafiles,
                        simpleNames=False, noTxt=False):
        with NamedTemporaryFile('w') as tempfile:
            for c in content:
                tempfile.write(c)
            tempfile.flush()
            if getsize(tempfile.name) > 0:
                expect(is_tarfile(tempfile.name)).to_be_truthy()
                try:
                    tf = TarFile(tempfile.name, 'r')
                    self._check_names(datafiles, tf.getnames(),
                                      rootdir, simpleNames, noTxt)
                finally:
                    tf.close()
            else:
                self._check_names(datafiles, [],
                                  rootdir, simpleNames, noTxt)

    def _check_zip_file(self, content, rootdir, datafiles,
                        simpleNames=False, noTxt=False):
        with NamedTemporaryFile('w') as tempfile:
            #import rpdb2; rpdb2.start_embedded_debugger("a")
            #import ipdb; ipdb.set_trace()
            for c in content:
                tempfile.write(c)
            tempfile.flush()
            # It should be a zip file
            expect(is_zipfile(tempfile.name)).to_be_truthy()
            try:
                zf = ZipFile(tempfile.name, 'r')
                self._check_names(datafiles, zf.namelist(),
                                  rootdir, simpleNames, noTxt)
            finally:
                zf.close()

    def _check_names(self, datafiles, names, rootdir, simpleNames, noTxt):
        # SimpleNames says if we expect basenames or pathnames
        # NoTxt says if we expect '.txt' files to be filtered out
        if not noTxt:
            expect(len(names)).to_equal(len(datafiles))
        for df in datafiles:
            if simpleNames:
                filename = df.filename
            else:
                filename = join(df.filename)  # TODO: update 'classic' to a
                # useful method and adapt test
            expect(filename in names).to_be(
                not (noTxt and filename.endswith('.txt')))

    def testDownload(self):
        client = Client()

        # check download for experiment1
        # disable zip test while zip is disabled
        # response = client.get('/download/experiment/%i/zip/' % \
        #                           self.experiment1.id)
        # self.assertEqual(response['Content-Disposition'],
        #                  'attachment; filename="experiment%s-complete.zip"'
        #                  % self.experiment1.id)
        # self.assertEqual(response.status_code, 200)
        # self._check_zip_file(
        #     response.streaming_content, str(self.experiment1.id),
        #     reduce(lambda x, y: x + y,
        #            [ds.datafile_set.all() \
        #                 for ds in self.experiment1.datasets.all()]))

        # check download for experiment1 as tar
        response = client.get('/download/experiment/%i/tar/test/' %
                              self.experiment1.id)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="%s-complete.tar"'
                         % self.experiment1.title.replace(' ', '_'))
        self.assertEqual(response.status_code, 200)
        self._check_tar_file(
            response.streaming_content, str(self.experiment1.title
                                            .replace(' ', '_')),
            reduce(lambda x, y: x + y,
                   [ds.datafile_set.all()
                    for ds in self.experiment1.datasets.all()]))

        # check download of file1
        response = client.get('/download/datafile/%i/' % self.datafile1.id)

        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="%s"'
                         % self.datafile1.filename)
        self.assertEqual(response.status_code, 200)
        response_content = ""
        for c in response.streaming_content:
            response_content += c
        self.assertEqual(response_content, 'Hello World!\n')

        # requesting file2 should be forbidden...
        response = client.get('/download/datafile/%i/' % self.datafile2.id)
        self.assertEqual(response.status_code, 403)

        # check dataset1 download
        # zips disabled for now
        # response = client.post('/download/datafiles/',
        #                        {'expid': self.experiment1.id,
        #                         'dataset': [self.dataset1.id],
        #                         'datafile': []})
        # self.assertEqual(response.status_code, 200)
        # self._check_zip_file(response.streaming_content, 'datasets',
        #                      self.dataset1.datafile_set.all())

        # check dataset1 download as tar
        response = client.post('/download/datafiles/',
                               {'expid': self.experiment1.id,
                                'dataset': [self.dataset1.id],
                                'datafile': [],
                                'comptype': 'tar'})
        self.assertEqual(response.status_code, 200)
        self._check_tar_file(response.streaming_content,
                             'Experiment 1-selection',
                             self.dataset1.datafile_set.all())

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
                                'datafile': [self.datafile1.id]})
        self.assertEqual(response.status_code, 200)
        self._check_tar_file(response.streaming_content,
                             'Experiment 1-selection',
                             [self.datafile1])

        # check datafile2 download via POST
        response = client.post('/download/datafiles/',
                               {'expid': self.experiment2.id,
                                'dataset': [],
                                'datafile': [self.datafile2.id]})
        self.assertEqual(response.status_code, 403)

        # Check datafile2 download with second experiment to "metadata only"
        self.experiment2.public_access = Experiment.PUBLIC_ACCESS_METADATA
        self.experiment2.save()
        response = client.get('/download/datafile/%i/' % self.datafile2.id)
        # Metadata-only means "no file access"!
        self.assertEqual(response.status_code, 403)

        # Check datafile2 download with second experiment to public
        self.experiment2.public_access = Experiment.PUBLIC_ACCESS_FULL
        self.experiment2.save()
        response = client.get('/download/datafile/%i/' % self.datafile2.id)
        self.assertEqual(response.status_code, 200)
        # This should be a TIFF (which often starts with "II\x2a\x00")
        self.assertEqual(response['Content-Type'], 'image/tiff')
        response_content = ""
        for c in response.streaming_content:
            response_content += c
        self.assertEqual(response_content[0:4], "II\x2a\x00")

        # check experiment zip download with alternative organization
        # disable zip for now
        # response = client.get('/download/experiment/%i/zip/test/' % \
        #                           self.experiment1.id)
        # self.assertEqual(response.status_code, 200)
        # self.assertEqual(response['Content-Disposition'],
        #                  'attachment; filename="%s-complete.zip"'
        #                  % self.experiment1.title)
        # self._check_zip_file(
        #     response.streaming_content, str(self.experiment1.id),
        #     reduce(lambda x, y: x + y,
        #            [ds.datafile_set.all() \
        #                 for ds in self.experiment1.datasets.all()]),
        #     simpleNames=True)

        # check experiment tar download with alternative organization
        response = client.get('/download/experiment/%i/tar/test/' %
                              self.experiment1.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="%s-complete.tar"'
                         % self.experiment1.title.replace(' ', '_'))
        self._check_tar_file(
            response.streaming_content, str(self.experiment1.id),
            reduce(lambda x, y: x + y,
                   [ds.datafile_set.all()
                    for ds in self.experiment1.datasets.all()]),
            simpleNames=True)

        # check experiment1 download with '.txt' filtered out (none left)
        response = client.get('/download/experiment/%i/tar/test2/' %
                              self.experiment1.id)
        self.assertEqual(response.status_code, 200)

        # check experiment2 download with '.txt' filtered out
        response = client.get('/download/experiment/%i/tar/test2/' %
                              self.experiment2.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="%s-complete.tar"'
                         % self.experiment2.title.replace(' ', '_'))
        self._check_tar_file(
            response.streaming_content, str(self.experiment2.id),
            reduce(lambda x, y: x + y,
                   [ds.datafile_set.all()
                    for ds in self.experiment2.datasets.all()]),
            simpleNames=True, noTxt=True)

        # check dataset1 download
        # zips disabled for now
        # response = client.post('/download/datafiles/',
        #                        {'expid': self.experiment1.id,
        #                         'dataset': [self.dataset1.id],
        #                         'datafile': [],
        #                         'comptype': 'zip',
        #                         'organization': 'test'})
        # self.assertEqual(response.status_code, 200)
        # self._check_zip_file(response.streaming_content, 'datasets',
        #                      self.dataset1.datafile_set.all(),
        #                      simpleNames=True)

    def testDatasetFile(self):
        return
        # check registered text file for physical file meta information
        df = DataFile.objects.get(pk=self.datafile1.id)

        try:
            from magic import Magic
            self.assertEqual(df.mimetype, 'text/plain; charset=us-ascii')
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
        self.assertEqual(df.size, str(13))
        self.assertEqual(df.md5sum, '8ddd8be4b179a529afa5f2ffae4b9858')

        # Now check we can calculate checksums and infer the mime type
        # for a JPG file.
        filename = abspath(join(dirname(__file__),
                                '../static/images/ands-logo-hi-res.jpg'))

        dataset = Dataset.objects.get(pk=self.dataset1.id)

        pdf1 = self._build_datafile(filename, basename(filename), dataset)
        self.assertEqual(pdf1.default_dfo.verify(), True)
        pdf1 = DataFile.objects.get(pk=pdf1.pk)

        try:
            from magic import Magic  # noqa
            self.assertEqual(pdf1.mimetype, 'image/jpeg')
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
        self.assertEqual(pdf1.size, str(14232))
        self.assertEqual(pdf1.md5sum, 'c450d5126ffe3d14643815204daf1bfb')

        # Now check that we can override the physical file meta information
        # We are setting size/checksums that don't match the actual file, so
        # the
        pdf2 = self._build_datafile(
            filename, filename, dataset,
            filename,
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',  # noqa
            size=0,
            # Empty string always has the same hash
            checksum='cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e')  # noqa
        self.assertEqual(pdf2.size, str(0))
        self.assertEqual(pdf2.md5sum, '')
        self.assertEqual(pdf2.get_preferred_replica().verify(), False)
        pdf2 = DataFile.objects.get(pk=pdf2.pk)
        try:
            from magic import Magic  # noqa
            self.assertEqual(pdf2.mimetype, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')  # noqa
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
        self.assertEqual(pdf2.size, str(0))
        self.assertEqual(pdf2.md5sum, '')

        pdf2.mimetype = ''
        pdf2.save()
        pdf2.get_preferred_replica().save()
        pdf2 = DataFile.objects.get(pk=pdf2.pk)

        try:
            from magic import Magic  # noqa
            self.assertEqual(pdf2.mimetype, 'application/pdf')
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass


def MyMapper(datafile, **kwargs):
    exclude = kwargs.get('exclude', None)
    if exclude and datafile.filename.endswith(exclude):
        return None
    return datafile.filename
