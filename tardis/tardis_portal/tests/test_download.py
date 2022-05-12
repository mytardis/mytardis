# -*- coding: utf-8 -*-

import hashlib
import re

from functools import reduce
from os import makedirs
from os.path import abspath, basename, join, exists, getsize
from shutil import rmtree
from zipfile import is_zipfile, ZipFile
from tarfile import is_tarfile, TarFile
from tempfile import NamedTemporaryFile
from urllib.parse import quote

from unittest.mock import patch

from django.test import override_settings
from django.test import TestCase
from django.test.client import Client

from django.conf import settings
from django.contrib.auth.models import User

from ..models.experiment import Experiment
from ..models.access_control import ExperimentACL, DatasetACL, DatafileACL

from ..models.dataset import Dataset
from ..models.datafile import DataFile, DataFileObject


try:
    from wand.image import Image  # pylint: disable=C0411

    IMAGEMAGICK_AVAILABLE = True
except (AttributeError, ImportError):
    IMAGEMAGICK_AVAILABLE = False


def get_size_and_sha512sum(testfile):
    with open(testfile, "rb") as f:
        contents = f.read()
        return (len(contents), hashlib.sha512(contents).hexdigest())


def _generate_test_image(testfile):
    if IMAGEMAGICK_AVAILABLE:
        with Image(filename="logo:") as img:
            img.format = "tiff"
            img.save(filename=testfile)
    else:
        # Apparently ImageMagick isn't installed...
        # Write a "fake" TIFF file
        with open(testfile, "w") as f:
            f.write("II\x2a\x00")
            f.close()


class DownloadTestCase(TestCase):
    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)

        # create a test user
        self.user = User.objects.create_user(
            username="DownloadTestUser", email="", password="secret"
        )

        # create a test user with read-only perms
        self.user2 = User.objects.create_user(
            username="ReadOnlyTestUser", email="", password="secret"
        )

        # create a public experiment
        self.experiment1 = Experiment(
            title="Experiment 1",
            created_by=self.user,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        self.experiment1.save()

        # create a non-public experiment
        self.experiment2 = Experiment(
            title="Experiment 2",
            created_by=self.user,
            public_access=Experiment.PUBLIC_ACCESS_NONE,
        )
        self.experiment2.save()

        self.exp_acl = ExperimentACL(
            user=self.user,
            experiment=self.experiment2,
            canRead=True,
            canDownload=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        self.exp_acl.save()

        self.exp_acl2 = ExperimentACL(
            user=self.user2,
            experiment=self.experiment2,
            canRead=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        self.exp_acl2.save()

        # dataset1 belongs to experiment1
        self.dataset1 = Dataset(description="dangerous;name")
        self.dataset1.save()
        self.dataset1.experiments.add(self.experiment1)
        self.dataset1.save()

        # dataset2 belongs to experiment2
        self.dataset2 = Dataset(description="terrible\nname")
        self.dataset2.save()
        self.dataset2.experiments.add(self.experiment2)
        self.dataset2.save()

        # absolute path first
        filename1 = "testfile.txt"
        filename2 = "testfile.tiff"
        self.dest1 = abspath(
            join(
                settings.FILE_STORE_PATH,
                "%s/%s/" % (self.experiment1.id, self.dataset1.id),
            )
        )
        self.dest2 = abspath(
            join(
                settings.FILE_STORE_PATH,
                "%s/%s/" % (self.experiment2.id, self.dataset2.id),
            )
        )
        if not exists(self.dest1):
            makedirs(self.dest1)
        if not exists(self.dest2):
            makedirs(self.dest2)

        testfile1 = abspath(join(self.dest1, filename1))
        with open(testfile1, "w") as f:
            f.write("Hello World!\n")
            f.close()

        testfile2 = abspath(join(self.dest2, filename2))
        _generate_test_image(testfile2)

        self.datafile1 = self._build_datafile(testfile1, filename1, self.dataset1)

        self.datafile2 = self._build_datafile(testfile2, filename2, self.dataset2)

    def _build_datafile(
        self, testfile, filename, dataset, checksum=None, size=None, mimetype=""
    ):
        filesize, sha512sum = get_size_and_sha512sum(testfile)
        datafile = DataFile(
            dataset=dataset,
            filename=filename,
            mimetype=mimetype,
            size=size if size is not None else filesize,
            sha512sum=(checksum if checksum else sha512sum),
        )
        datafile.save()
        dfo = DataFileObject(
            datafile=datafile, storage_box=datafile.get_default_storage_box()
        )
        dfo.save()
        with open(testfile, "rb") as sourcefile:
            dfo.file_object = sourcefile
        return DataFile.objects.get(pk=datafile.pk)

    def tearDown(self):
        self.user.delete()
        self.user2.delete()
        self.experiment1.delete()
        self.experiment2.delete()
        rmtree(self.dest1)
        rmtree(self.dest2)

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def testView(self, mock_webpack_get_bundle):
        client = Client()

        # check view of file1
        response = client.get("/datafile/view/%i/" % self.datafile1.id)

        self.assertEqual(
            response["Content-Disposition"],
            'inline; filename="%s"' % self.datafile1.filename,
        )
        self.assertEqual(response.status_code, 200)
        response_content = b"".join(response.streaming_content)
        self.assertEqual(response_content, b"Hello World!\n")

        # check view of file2
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        # Should be forbidden
        self.assertEqual(response.status_code, 403)

        # test that created_by user can view file2
        client.login(username="DownloadTestUser", password="secret")
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 200)
        client.logout()

        # test that ReadOnly user cannot view file2 (as it is effectively a download)
        client.login(username="ReadOnlyTestUser", password="secret")
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        # Should be forbidden
        self.assertEqual(response.status_code, 403)
        client.logout()

        self.experiment2.public_access = Experiment.PUBLIC_ACCESS_FULL
        self.experiment2.save()
        # check view of file2 again
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 200)

        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # The following behaviour relies on ImageMagick
        if IMAGEMAGICK_AVAILABLE:
            # file2 should have a ".png" filename
            self.assertEqual(
                response["Content-Disposition"],
                'inline; filename="%s"' % (self.datafile2.filename + ".png"),
            )
            # file2 should be a PNG
            self.assertEqual(response["Content-Type"], "image/png")
            png_signature = b"\x89PNG\r\n\x1a\n"
            self.assertEqual(response.content[0:8], png_signature)
        else:
            # file2 should have a ".tiff" filename
            self.assertEqual(
                response["Content-Disposition"],
                'inline; filename="%s"' % (self.datafile2.filename),
            )
            # file2 should be a TIFF
            self.assertEqual(response["Content-Type"], "image/tiff")
            tiff_signature = "II\x2a\x00"
            self.assertEqual(response.content[0:4], tiff_signature)

    @override_settings(ONLY_EXPERIMENT_ACLS=False)
    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def testView_micro(self, mock_webpack_get_bundle):
        client = Client()

        # check view of file1
        response = client.get("/datafile/view/%i/" % self.datafile1.id)
        # Public Experiment does not imply public Dataset or Datafile
        self.assertEqual(response.status_code, 403)

        self.dataset1.public_access = Dataset.PUBLIC_ACCESS_FULL
        self.dataset1.save()

        # check view of file1
        response = client.get("/datafile/view/%i/" % self.datafile1.id)
        # Public Experiment and Dataset still does not imply public Datafile
        self.assertEqual(response.status_code, 403)

        self.datafile1.public_access = DataFile.PUBLIC_ACCESS_FULL
        self.datafile1.save()

        # check view of file1
        response = client.get("/datafile/view/%i/" % self.datafile1.id)
        # Finally Datafile should now be public and visible
        self.assertEqual(
            response["Content-Disposition"],
            'inline; filename="%s"' % self.datafile1.filename,
        )
        self.assertEqual(response.status_code, 200)
        response_content = b"".join(response.streaming_content)
        self.assertEqual(response_content, b"Hello World!\n")

        # check view of file2
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        # Should be forbidden
        self.assertEqual(response.status_code, 403)

        # test that created_by user cannot view file2 despite ExperimentACL
        client.login(username="DownloadTestUser", password="secret")
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 403)
        client.logout()

        self.set_acl = DatasetACL(
            user=self.user,
            dataset=self.dataset2,
            canRead=True,
            canDownload=True,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
        )
        self.set_acl.save()

        # test that created_by user still cannot view file2 despite DatasetACL
        client.login(username="DownloadTestUser", password="secret")
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 403)
        client.logout()

        self.file_acl = DatafileACL(
            user=self.user,
            datafile=self.datafile2,
            canRead=True,
            canDownload=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        self.file_acl.save()

        # test that created_by user can view file2
        client.login(username="DownloadTestUser", password="secret")
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 200)
        client.logout()

        self.set_acl2 = DatasetACL(
            user=self.user2,
            dataset=self.dataset2,
            canRead=True,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
        )
        self.set_acl2.save()
        self.file_acl2 = DatafileACL(
            user=self.user2,
            datafile=self.datafile2,
            canRead=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        self.file_acl2.save()

        # test that ReadOnly user cannot view file2 (as it is effectively a download)
        client.login(username="ReadOnlyTestUser", password="secret")
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        # Should be forbidden
        self.assertEqual(response.status_code, 403)
        client.logout()

        self.experiment2.public_access = Experiment.PUBLIC_ACCESS_FULL
        self.experiment2.save()

        # check view of file2 again, should still be 403 as File not public
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 403)

        self.datafile2.public_access = DataFile.PUBLIC_ACCESS_FULL
        self.datafile2.save()

        # check view of file2 again, should now be 200 as File is public
        response = client.get("/datafile/view/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 403)

        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # The following behaviour relies on ImageMagick
        if IMAGEMAGICK_AVAILABLE:
            # file2 should have a ".png" filename
            self.assertEqual(
                response["Content-Disposition"],
                'inline; filename="%s"' % (self.datafile2.filename + ".png"),
            )
            # file2 should be a PNG
            self.assertEqual(response["Content-Type"], "image/png")
            png_signature = b"\x89PNG\r\n\x1a\n"
            self.assertEqual(response.content[0:8], png_signature)
        else:
            # file2 should have a ".tiff" filename
            self.assertEqual(
                response["Content-Disposition"],
                'inline; filename="%s"' % (self.datafile2.filename),
            )
            # file2 should be a TIFF
            self.assertEqual(response["Content-Type"], "image/tiff")
            tiff_signature = "II\x2a\x00"
            self.assertEqual(response.content[0:4], tiff_signature)

    def _check_tar_file(
        self, content, rootdir, datafiles, simpleNames=False, noTxt=False
    ):
        with NamedTemporaryFile("wb") as tempfile:
            for c in content:
                tempfile.write(c)
            tempfile.flush()
            if getsize(tempfile.name) > 0:
                self.assertTrue(is_tarfile(tempfile.name))
                with TarFile(tempfile.name, "r") as tf:
                    try:
                        self._check_names(
                            datafiles, tf.getnames(), rootdir, simpleNames, noTxt
                        )
                    finally:
                        tf.close()
            else:
                self._check_names(datafiles, [], rootdir, simpleNames, noTxt)

    def _check_zip_file(
        self, content, rootdir, datafiles, simpleNames=False, noTxt=False
    ):
        with NamedTemporaryFile("w") as tempfile:
            for c in content:
                tempfile.write(c)
            tempfile.flush()
            # It should be a zip file
            self.assertTrue(is_zipfile(tempfile.name))
            with ZipFile(tempfile.name, "r") as zf:
                try:
                    self._check_names(
                        datafiles, zf.namelist(), rootdir, simpleNames, noTxt
                    )
                finally:
                    zf.close()

    def _check_names(self, datafiles, names, rootdir, simpleNames, noTxt):
        # SimpleNames says if we expect basenames or pathnames
        # NoTxt says if we expect '.txt' files to be filtered out
        for name in names:
            pattern = re.compile("\n|;")
            self.assertFalse(pattern.search(name))
        self.assertEqual(len(names), len(datafiles))

    @patch("webpack_loader.loader.WebpackLoader.get_bundle")
    def testDownload(self, mock_webpack_get_bundle):
        client = Client()

        # check download for experiment1 as tar
        response = client.get("/download/experiment/%i/tar/" % self.experiment1.id)
        if settings.EXP_SPACES_TO_UNDERSCORES:
            exp1_title = self.experiment1.title.replace(" ", "_")
        else:
            exp1_title = self.experiment1.title
        exp1_title = quote(exp1_title, safe=settings.SAFE_FILESYSTEM_CHARACTERS)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="%s-complete.tar"' % exp1_title,
        )
        self.assertEqual(response.status_code, 200)
        self._check_tar_file(
            response.streaming_content,
            exp1_title,
            reduce(
                lambda x, y: x + y,
                [ds.datafile_set.all() for ds in self.experiment1.datasets.all()],
            ),
        )

        # check download of file1
        response = client.get("/download/datafile/%i/" % self.datafile1.id)

        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="%s"' % self.datafile1.filename,
        )
        self.assertEqual(response.status_code, 200)
        response_content = b"".join(response.streaming_content)
        self.assertEqual(response_content, b"Hello World!\n")

        # requesting file2 should be forbidden...
        response = client.get("/download/datafile/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 403)

        # test that created_by user can download file2
        client.login(username="DownloadTestUser", password="secret")
        response = client.get("/download/datafile/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 200)
        client.logout()

        # test that ReadOnly user cannot download file2
        client.login(username="ReadOnlyTestUser", password="secret")
        response = client.get("/download/datafile/%i/" % self.datafile2.id)
        # Should be forbidden
        self.assertEqual(response.status_code, 403)
        client.logout()

        # check dataset1 download as tar
        response = client.post(
            "/download/datafiles/",
            {
                "expid": self.experiment1.id,
                "dataset": [self.dataset1.id],
                "datafile": [],
                "comptype": "tar",
            },
        )
        self.assertEqual(response.status_code, 200)
        self._check_tar_file(
            response.streaming_content,
            "Experiment 1-selection",
            self.dataset1.datafile_set.all(),
        )

        # check dataset2 download
        response = client.post(
            "/download/datafiles/",
            {
                "expid": self.experiment2.id,
                "dataset": [self.dataset2.id],
                "datafile": [],
            },
        )
        self.assertEqual(response.status_code, 302)

        # check datafile1 download via POST
        response = client.post(
            "/download/datafiles/",
            {
                "expid": self.experiment1.id,
                "dataset": [],
                "datafile": [self.datafile1.id],
            },
        )
        self.assertEqual(response.status_code, 200)
        self._check_tar_file(
            response.streaming_content, "Experiment 1-selection", [self.datafile1]
        )

        # check datafile2 download via POST
        response = client.post(
            "/download/datafiles/",
            {
                "expid": self.experiment2.id,
                "dataset": [],
                "datafile": [self.datafile2.id],
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check datafile2 download with second experiment to "metadata only"
        self.experiment2.public_access = Experiment.PUBLIC_ACCESS_METADATA
        self.experiment2.save()
        response = client.get("/download/datafile/%i/" % self.datafile2.id)
        # Metadata-only means "no file access"!
        self.assertEqual(response.status_code, 403)

        # Check datafile2 download with second experiment to public
        self.experiment2.public_access = Experiment.PUBLIC_ACCESS_FULL
        self.experiment2.save()
        response = client.get("/download/datafile/%i/" % self.datafile2.id)
        self.assertEqual(response.status_code, 200)
        # This should be a TIFF (which often starts with "II\x2a\x00")
        self.assertEqual(response["Content-Type"], "image/tiff")
        response_content = b"".join(response.streaming_content)
        self.assertEqual(response_content[0:4], b"II\x2a\x00")

        # check experiment tar download with alternative organization
        response = client.get("/download/experiment/%i/tar/" % self.experiment1.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="%s-complete.tar"' % exp1_title,
        )
        self._check_tar_file(
            response.streaming_content,
            str(self.experiment1.id),
            reduce(
                lambda x, y: x + y,
                [ds.datafile_set.all() for ds in self.experiment1.datasets.all()],
            ),
            simpleNames=True,
        )

        # check experiment1 download with '.txt' filtered out (none left)
        response = client.get("/download/experiment/%i/tar/" % self.experiment1.id)
        self.assertEqual(response.status_code, 200)

        # check experiment2 download with '.txt' filtered out
        if settings.EXP_SPACES_TO_UNDERSCORES:
            exp2_title = self.experiment2.title.replace(" ", "_")
        else:
            exp2_title = self.experiment2.title
        exp2_title = quote(exp2_title, safe=settings.SAFE_FILESYSTEM_CHARACTERS)
        response = client.get("/download/experiment/%i/tar/" % self.experiment2.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="%s-complete.tar"' % exp2_title,
        )
        self._check_tar_file(
            response.streaming_content,
            str(self.experiment2.id),
            reduce(
                lambda x, y: x + y,
                [ds.datafile_set.all() for ds in self.experiment2.datasets.all()],
            ),
            simpleNames=True,
            noTxt=True,
        )

    def testDatasetFile(self):
        # check registered text file for physical file meta information
        df = DataFile.objects.get(
            pk=self.datafile1.id
        )  # skipping test # noqa # pylint: disable=W0101

        try:
            from magic import Magic  # pylint: disable=W0611

            self.assertEqual(df.mimetype, "text/plain; charset=us-ascii")
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
        self.assertEqual(df.size, 13)
        self.assertEqual(df.md5sum, "8ddd8be4b179a529afa5f2ffae4b9858")

        # Now check we can calculate checksums and infer the mime type
        # for a JPG file.
        filename = "tardis/tardis_portal/tests/test_data/ands-logo-hi-res.jpg"

        dataset = Dataset.objects.get(pk=self.dataset1.id)

        pdf1 = self._build_datafile(filename, basename(filename), dataset)
        self.assertEqual(pdf1.file_objects.get().verify(), True)
        pdf1 = DataFile.objects.get(pk=pdf1.pk)

        try:
            from magic import Magic  # pylint: disable=W0611

            self.assertEqual(pdf1.mimetype, "image/jpeg")
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
        self.assertEqual(pdf1.size, 14232)
        self.assertEqual(pdf1.md5sum, "c450d5126ffe3d14643815204daf1bfb")

        # Now check that we can override the physical file meta information
        # We are setting size/checksums that don't match the actual file, so
        # the
        pdf2 = self._build_datafile(
            filename,
            filename,
            dataset,
            checksum=(
                "cf83e1357eefb8bdf1542850d66d800"
                "7d620e4050b5715dc83f4a921d36ce9"
                "ce47d0d13c5d85f2b0ff8318d2877ee"
                "c2f63b931bd47417a81a538327af927"
                "da3e"
            ),
            size=0,
            mimetype=(
                "application/vnd.openxmlformats-"
                "officedocument.presentationml."
                "presentation"
            ),
        )
        self.assertEqual(pdf2.size, 0)
        self.assertEqual(pdf2.md5sum, "")
        self.assertEqual(pdf2.file_objects.get().verified, False)
        pdf2 = DataFile.objects.get(pk=pdf2.pk)
        try:
            from magic import Magic  # pylint: disable=W0611

            self.assertEqual(
                pdf2.mimetype,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.presentationml."
                    "presentation"
                ),
            )
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
        self.assertEqual(pdf2.size, 0)
        self.assertEqual(pdf2.md5sum, "")

        pdf2.mimetype = ""
        pdf2.save()
        pdf2.file_objects.get().save()
        pdf2 = DataFile.objects.get(pk=pdf2.pk)

        try:
            from magic import Magic  # pylint: disable=W0611

            self.assertEqual(pdf2.mimetype, "application/pdf")
        except:
            # XXX Test disabled because lib magic can't be loaded
            pass
