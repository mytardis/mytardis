import hashlib
import os
from io import BytesIO
from tarfile import TarFile
from tempfile import NamedTemporaryFile
from unittest import skipIf
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from ..models.datafile import DataFile
from ..models.dataset import Dataset
from ..models.experiment import Experiment


class TarDownloadTestCase(TestCase):
    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        # create user
        self.testuser = User(username="testuser")
        self.testuser.save()

        # create test experiment
        self.exp = Experiment(
            title="tar download test" * 15,
            created_by=self.testuser,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
        )
        self.exp.save()

        # create test dataset
        self.ds = self.exp.datasets.create(description="testing tar download dataset")

        if not settings.ONLY_EXPERIMENT_ACLS:
            self.ds.public_access = Dataset.PUBLIC_ACCESS_FULL
            self.ds.save()

        datafile_content = b"\n".join([b"some data %d" % i for i in range(1000)])
        filesize = len(datafile_content)
        md5sum = hashlib.md5(datafile_content).hexdigest()
        # create test datafiles and datafile objects
        self.dfs = []
        for i in range(20):
            df = self.ds.datafile_set.create(
                filename="testfile%d.txt" % i,
                mimetype="text/plain",
                size=filesize,
                md5sum=md5sum,
                directory="/".join(["testdir%d" % i for i in range(i, i + 4)]),
            )
            df.file_object = BytesIO(datafile_content)
            df.refresh_from_db()
            self.dfs.append(df)

        # mock client
        self.client = Client()

    def tearDown(self):
        # delete created objects and files

        [ds.delete() for ds in self.exp.datasets.all()]
        self.exp.delete()

    @skipIf(settings.ONLY_EXPERIMENT_ACLS is False, "skipping Macro ACL specific test")
    def test_tar_experiment_download_macro(self):
        self.assertTrue(all(df.verified for df in self.dfs))
        response = self.client.get(
            reverse(
                "tardis.tardis_portal.download.streaming_download_experiment",
                args=(self.exp.id, "tar"),
            )
        )
        with NamedTemporaryFile("w") as tarfile:
            for c in response.streaming_content:
                tarfile.write(c.decode())
            tarfile.flush()
            self.assertEqual(
                int(response["Content-Length"]), os.stat(tarfile.name).st_size
            )
            with TarFile(tarfile.name) as tf:
                if settings.EXP_SPACES_TO_UNDERSCORES:
                    exp_title = self.exp.title.replace(" ", "_")
                else:
                    exp_title = self.exp.title
                exp_title = quote(exp_title, safe=settings.SAFE_FILESYSTEM_CHARACTERS)
                for df in self.dfs:
                    full_path = os.path.join(
                        exp_title,
                        quote(
                            self.ds.description,
                            safe=settings.SAFE_FILESYSTEM_CHARACTERS,
                        ),
                        df.directory,
                        df.filename,
                    )
                    # docker has a file path limit of ~240 characters
                    if os.environ.get("DOCKER_BUILD", "false") != "true":
                        tf.extract(full_path, "/tmp")
                        self.assertEqual(
                            os.stat(os.path.join("/tmp", full_path)).st_size,
                            int(df.size),
                        )

    @skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
    def test_tar_experiment_download_micro(self):
        self.assertTrue(all(df.verified for df in self.dfs))
        response = self.client.get(
            reverse(
                "tardis.tardis_portal.download.streaming_download_experiment",
                args=(self.exp.id, "tar"),
            )
        )
        # Redirect with error as no downloadable Datafiles
        self.assertEqual(response.status_code, 302)

        # Make every other datafile public/downloadable
        for df in self.dfs[::2]:
            df.public_access = DataFile.PUBLIC_ACCESS_FULL
            df.save()

        # Try downloading again
        response = self.client.get(
            reverse(
                "tardis.tardis_portal.download.streaming_download_experiment",
                args=(self.exp.id, "tar"),
            )
        )
        with NamedTemporaryFile("w") as tarfile:
            for c in response.streaming_content:
                tarfile.write(c.decode())
            tarfile.flush()
            self.assertEqual(
                int(response["Content-Length"]), os.stat(tarfile.name).st_size
            )
            with TarFile(tarfile.name) as tf:
                if settings.EXP_SPACES_TO_UNDERSCORES:
                    exp_title = self.exp.title.replace(" ", "_")
                else:
                    exp_title = self.exp.title
                exp_title = quote(exp_title, safe=settings.SAFE_FILESYSTEM_CHARACTERS)
                for df in self.dfs[::2]:  # Only every other file
                    full_path = os.path.join(
                        exp_title,
                        quote(
                            self.ds.description,
                            safe=settings.SAFE_FILESYSTEM_CHARACTERS,
                        ),
                        df.directory,
                        df.filename,
                    )
                    # docker has a file path limit of ~240 characters
                    if os.environ.get("DOCKER_BUILD", "false") != "true":
                        tf.extract(full_path, "/tmp")
                        self.assertEqual(
                            os.stat(os.path.join("/tmp", full_path)).st_size,
                            int(df.size),
                        )
