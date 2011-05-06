# -*- coding: utf-8 -*-

from os import makedirs
from os.path import abspath, basename, dirname, join, exists
from shutil import rmtree

from django.test import TestCase
from django.test.client import Client

from django.conf import settings
from django.contrib.auth.models import User

from tardis.tardis_portal.models import Experiment, Dataset, Dataset_File


class DownloadTestCase(TestCase):

    def setUp(self):
        # create a test user
        self.user = User.objects.create_user(username='DownloadTestUser',
                                             email='',
                                             password='secret')

        # create a public experiment
        self.experiment1 = Experiment(title='Experiment 1',
                                      created_by=self.user,
                                      public=True)
        self.experiment1.save()

        # create a non-public experiment
        self.experiment2 = Experiment(title='Experiment 2',
                                      created_by=self.user,
                                      public=False)
        self.experiment2.save()

        # dataset1 belongs to experiment1
        self.dataset1 = Dataset(experiment=self.experiment1)
        self.dataset1.save()

        # dataset2 belongs to experiment2
        self.dataset2 = Dataset(experiment=self.experiment2)
        self.dataset2.save()

        # absolute path first
        filename = 'testfile.txt'
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

        testfile1 = abspath(join(self.dest1, filename))
        f = open(testfile1, 'w')
        f.write("Hello World!\n")
        f.close()

        testfile2 = abspath(join(self.dest2, filename))
        f = open(testfile2, 'w')
        f.write("Hello World!\n")
        f.close()

        self.dataset_file1 = Dataset_File(dataset=self.dataset1,
                                          filename=filename,
                                          protocol='tardis',
                                          url='tardis://%s' % filename)
        self.dataset_file1.save()

        self.dataset_file2 = Dataset_File(dataset=self.dataset2,
                                          filename=basename(filename),
                                          protocol='tardis',
                                          url='tardis://%s' % filename)
        self.dataset_file2.save()

    def tearDown(self):
        self.user.delete()
        self.experiment1.delete()
        self.experiment2.delete()
        rmtree(self.dest1)
        rmtree(self.dest2)

    def testDownload(self):
        client = Client()

        # check download for experiment1
        response = client.get('/download/experiment/%i/zip/' % self.experiment1.id)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="experiment%s-complete.zip"'
                         % self.experiment1.id)
        self.assertEqual(response.status_code, 200)

        # check download of file1
        response = client.get('/download/datafile/%i/' % self.dataset_file1.id)

        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="%s"'
                         % self.dataset_file2.filename)
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

        # check datafile2 download via POST
        response = client.post('/download/datafiles/',
                               {'expid': self.experiment2.id,
                                'dataset': [],
                                'datafile': [self.dataset_file2.id]})
        self.assertEqual(response.status_code, 403)

    def testDatasetFile(self):

        # check registered text file for physical file meta information
        df = Dataset_File.objects.get(pk=self.dataset_file1.id)

        try:
            from magic import Magic
            self.assertEqual(df.mimetype, 'text/plain; charset=us-ascii')
        except:
            # XXX Test disabled becuse lib magic can't be loaded
            pass
        self.assertEqual(df.size, str(13))
        self.assertEqual(df.md5sum, '8ddd8be4b179a529afa5f2ffae4b9858')

        # now check a pdf file
        filename = join(abspath(dirname(__file__)),
                        '../site_media/downloads/DatasetDepositionGuide.pdf')

        dataset = Dataset.objects.get(pk=self.dataset1.id)

        pdf1 = Dataset_File(dataset=dataset,
                            filename=basename(filename),
                            url='file://%s' % filename,
                            protocol='file')
        pdf1.save()
        try:
            from magic import Magic
            self.assertEqual(pdf1.mimetype, 'application/pdf')
        except:
            # XXX Test disabled becuse lib magic can't be loaded
            pass
        self.assertEqual(pdf1.size, str(1008475))
        self.assertEqual(pdf1.md5sum, '9192b3d3e0056412b1d21d3e33562eba')

        # now check that we can override the physical file meta information
        pdf2 = Dataset_File(dataset=dataset,
                            filename=basename(filename),
                            url='file://%s' % filename,
                            protocol='file',
                            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                            size=str(0),
                            md5sum='md5sum')
        pdf2.save()
        try:
            from magic import Magic
            self.assertEqual(pdf2.mimetype, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
        except:
            # XXX Test disabled becuse lib magic can't be loaded
            pass
        self.assertEqual(pdf2.size, str(0))
        self.assertEqual(pdf2.md5sum, 'md5sum')

        pdf2.mimetype = ''
        pdf2.save()

        try:
            from magic import Magic
            self.assertEqual(pdf2.mimetype, 'application/pdf')
        except:
            # XXX Test disabled becuse lib magic can't be loaded
            pass
