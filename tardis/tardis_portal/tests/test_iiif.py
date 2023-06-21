import json
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from lxml import etree
from wand.image import Image

from ..models.access_control import DatafileACL, DatasetACL, ExperimentACL
from ..models.datafile import DataFile, compute_checksums
from ..models.dataset import Dataset
from ..models.experiment import Experiment

"""
Tests for IIIF API.

http://library.stanford.edu/iiif/image-api/

"""


def _create_datafile():
    user = User.objects.create_user("testuser", "user@email.test", "pwd")
    user.save()

    full_access = Experiment.PUBLIC_ACCESS_FULL
    experiment = Experiment.objects.create(
        title="IIIF Test", created_by=user, public_access=full_access
    )
    experiment.save()
    ExperimentACL(
        experiment=experiment,
        user=user,
        isOwner=True,
        canRead=True,
        canDownload=True,
        canWrite=True,
        canDelete=True,
        canSensitive=True,
        aclOwnershipType=ExperimentACL.OWNER_OWNED,
    ).save()
    dataset = Dataset()
    dataset.save()
    dataset.experiments.add(experiment)
    dataset.save()
    dataset.public_access = Dataset.PUBLIC_ACCESS_FULL
    dataset.save()

    if not settings.ONLY_EXPERIMENT_ACLS:
        DatasetACL(
            dataset=dataset,
            user=user,
            isOwner=True,
            canRead=True,
            canDownload=True,
            canWrite=True,
            canDelete=True,
            canSensitive=True,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
        ).save()

    # Create new Datafile
    tempfile = TemporaryUploadedFile("iiif_stored_file", None, None, None)
    with Image(filename="magick:rose") as img:
        img.format = "tiff"
        img.save(file=tempfile.file)
        tempfile.file.flush()
    datafile = DataFile(
        dataset=dataset,
        size=os.path.getsize(tempfile.file.name),
        filename="iiif_named_file",
        mimetype="image/tiff",
    )
    compute_md5 = getattr(settings, "COMPUTE_MD5", True)
    compute_sha512 = getattr(settings, "COMPUTE_SHA512", False)
    checksums = compute_checksums(
        open(tempfile.file.name, "rb"),  # pylint: disable=R1732
        compute_md5=compute_md5,
        compute_sha512=compute_sha512,
    )
    if compute_md5:
        datafile.md5sum = checksums["md5sum"]
    if compute_sha512:
        datafile.sha512sum = checksums["sha512sum"]
    datafile.save()
    datafile.public_access = DataFile.PUBLIC_ACCESS_FULL
    datafile.save()

    if not settings.ONLY_EXPERIMENT_ACLS:
        DatafileACL(
            datafile=datafile,
            user=user,
            isOwner=True,
            canRead=True,
            canDownload=True,
            canWrite=True,
            canDelete=True,
            canSensitive=True,
            aclOwnershipType=DatafileACL.OWNER_OWNED,
        ).save()

    datafile.file_object = tempfile
    return datafile


def _check_compliance_level(testCase, response):
    """
    Current complies with Level 1 API, so should assert no more.
    """
    testCase.assertRegex(
        response["Link"],
        r"\<http:\/\/library.stanford.edu\/iiif\/image-api\/"
        + r'compliance.html#level[01]\>;rel="compliesTo"',
        "Compliance header missing",
    )


class Level0TestCase(TestCase):
    """As per: http://library.stanford.edu/iiif/image-api/compliance.html"""

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.datafile = _create_datafile()
        self.width = 70
        self.height = 46

    def testCanGetInfoAsXML(self):
        client = Client()
        kwargs = {"datafile_id": self.datafile.id, "format": "xml"}
        response = client.get(
            reverse("tardis.tardis_portal.iiif.download_info", kwargs=kwargs)
        )
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        nsmap = {"i": "http://library.stanford.edu/iiif/image-api/ns/"}
        xml = etree.fromstring(response.content.decode())
        identifier = xml.xpath("/i:info/i:identifier", namespaces=nsmap)[0]
        self.assertEqual(int(identifier.text), self.datafile.id)
        height = xml.xpath("/i:info/i:height", namespaces=nsmap)[0]
        self.assertEqual(int(height.text), self.height)
        width = xml.xpath("/i:info/i:width", namespaces=nsmap)[0]
        self.assertEqual(int(width.text), self.width)
        # Check compliance level
        _check_compliance_level(self, response)

    def testCanGetInfoAsJSON(self):
        client = Client()
        kwargs = {"datafile_id": self.datafile.id, "format": "json"}
        response = client.get(
            reverse("tardis.tardis_portal.iiif.download_info", kwargs=kwargs)
        )
        self.assertEqual(response.status_code, 200)
        # Check the response content is good
        data = json.loads(response.content.decode())
        self.assertEqual(data["identifier"], self.datafile.id)
        self.assertEqual(data["height"], self.height)
        self.assertEqual(data["width"], self.width)
        # Check compliance level
        _check_compliance_level(self, response)

    def testCanGetOriginalImage(self):
        client = Client()
        kwargs = {
            "datafile_id": self.datafile.id,
            "region": "full",
            "size": "full",
            "rotation": "0",
            "quality": "native",
        }
        response = client.get(
            reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
        )
        self.assertEqual(response.status_code, 200)
        with Image(blob=response.content) as img:
            self.assertEqual(img.format, "TIFF")
            self.assertEqual(img.width, self.width)
            self.assertEqual(img.height, self.height)
        # Check compliance level
        _check_compliance_level(self, response)


class Level1TestCase(TestCase):
    """As per: http://library.stanford.edu/iiif/image-api/compliance.html"""

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.datafile = _create_datafile()
        self.width = 70
        self.height = 46

    def testCanGetJpegFormat(self):
        client = Client()
        kwargs = {
            "datafile_id": self.datafile.id,
            "region": "full",
            "size": "full",
            "rotation": "0",
            "quality": "native",
            "format": "jpg",
        }
        response = client.get(
            reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
        )
        self.assertEqual(response.status_code, 200)
        with Image(blob=response.content) as img:
            self.assertEqual(img.format, "JPEG")
            self.assertEqual(img.width, self.width)
            self.assertEqual(img.height, self.height)
        # Check compliance level
        _check_compliance_level(self, response)

    def testHandleRegions(self):
        client = Client()
        # Inside box
        kwargs = {
            "datafile_id": self.datafile.id,
            "region": "15,10,25,20",
            "size": "full",
            "rotation": "0",
            "quality": "native",
            "format": "jpg",
        }
        response = client.get(
            reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
        )
        self.assertEqual(response.status_code, 200)
        with Image(blob=response.content) as img:
            self.assertEqual(img.width, 25)
            self.assertEqual(img.height, 20)
        # Partly outside box
        kwargs = {
            "datafile_id": self.datafile.id,
            "region": "60,41,20,20",
            "size": "full",
            "rotation": "0",
            "quality": "native",
            "format": "jpg",
        }
        response = client.get(
            reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
        )
        self.assertEqual(response.status_code, 200)
        with Image(blob=response.content) as img:
            self.assertEqual(img.width, 10)
            self.assertEqual(img.height, 5)
        # Check compliance level
        _check_compliance_level(self, response)

    def testHandleSizing(self):
        client = Client()

        def get_with_size(sizearg):
            kwargs = {
                "datafile_id": self.datafile.id,
                "region": "full",
                "size": sizearg,
                "rotation": "0",
                "quality": "native",
                "format": "jpg",
            }
            response = client.get(
                reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
            )
            self.assertEqual(response.status_code, 200)
            return response

        permutations = [
            # Width (aspect ratio preserved)
            {"arg": "50,", "width": 50, "height": 33},
            # Height (aspect ratio preserved)
            {"arg": ",30", "width": 46, "height": 30},
            # Percent size (aspect ratio preserved)
            {"arg": "pct:50", "width": 35, "height": 23},
        ]
        for data in permutations:
            response = get_with_size(data["arg"])
            with Image(blob=response.content) as img:
                self.assertEqual(img.width, data["width"])
                self.assertEqual(img.height, data["height"])

    def testHandleRotation(self):
        client = Client()

        def get_with_rotation(rotation):
            kwargs = {
                "datafile_id": self.datafile.id,
                "region": "full",
                "size": "full",
                "rotation": rotation,
                "quality": "native",
                "format": "jpg",
            }
            response = client.get(
                reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
            )
            self.assertEqual(response.status_code, 200)
            return response

        rotations = [get_with_rotation(i) for i in [0, 90, 180, 270]]
        for response in rotations[::2]:
            with Image(blob=response.content) as img:
                self.assertEqual(img.width, self.width)
                self.assertEqual(img.height, self.height)
        for response in rotations[1::2]:
            with Image(blob=response.content) as img:
                self.assertEqual(img.width, self.height)
                self.assertEqual(img.height, self.width)


class Level2TestCase(TestCase):
    """As per: http://library.stanford.edu/iiif/image-api/compliance.html"""

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.datafile = _create_datafile()
        self.width = 70
        self.height = 46

    def testCanGetRequiredFormats(self):
        client = Client()
        # not testing jp2, as this does not work on all platforms
        for ext, format in [("jpg", "JPEG"), ("png", "PNG")]:
            kwargs = {
                "datafile_id": self.datafile.id,
                "region": "full",
                "size": "full",
                "rotation": "0",
                "quality": "native",
                "format": ext,
            }
            response = client.get(
                reverse("tardis.tardis_portal.iiif." + "download_image", kwargs=kwargs)
            )
            self.assertEqual(response.status_code, 200)
            with Image(blob=response.content) as img:
                self.assertEqual(img.format, format)
                self.assertEqual(img.width, self.width)
                self.assertEqual(img.height, self.height)
            # Check compliance level
            _check_compliance_level(self, response)

    def testHandleSizing(self):
        client = Client()

        def get_with_size(sizearg):
            kwargs = {
                "datafile_id": self.datafile.id,
                "region": "full",
                "size": sizearg,
                "rotation": "0",
                "quality": "native",
                "format": "jpg",
            }
            response = client.get(
                reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
            )
            self.assertEqual(response.status_code, 200)
            return response

        permutations = [
            # Exact dimensions *without* aspect ratio preserved
            {"arg": "16,16", "width": 16, "height": 16},
            # Maximum dimensions (aspect ratio preserved)
            {"arg": "!16,16", "width": 16, "height": 11},
            {"arg": "!90,11", "width": 17, "height": 11},
            {"arg": "!16,10", "width": 15, "height": 10},
        ]
        for data in permutations:
            response = get_with_size(data["arg"])
            with Image(blob=response.content) as img:
                self.assertEqual(img.width, data["width"])
                self.assertEqual(img.height, data["height"])

    # def testCanGetRequiredQualities(self):
    #     client = Client()
    #     data = [('native', 3019),
    #             ('color', 3019),
    #             ('grey', 205),
    #             ('bitonal', 2)]
    #     # Not currently implemented
    #     raise SkipTest


class ExtraTestCases(TestCase):
    """As per: http://library.stanford.edu/iiif/image-api/compliance.html"""

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.datafile = _create_datafile()
        self.width = 70
        self.height = 46

    def testInfoHasEtags(self):
        client = Client()
        for format_ in ("json", "xml"):
            kwargs = {"datafile_id": self.datafile.id, "format": format_}
            url = reverse("tardis.tardis_portal.iiif.download_info", kwargs=kwargs)
            response = client.get(url)
            self.assertEqual(response.status_code, 200)
            # Check etag exists
            self.assertIn("Etag", response, "Info should have an etag")

    def testImageHasEtags(self):
        client = Client()
        kwargs = {
            "datafile_id": self.datafile.id,
            "region": "full",
            "size": "full",
            "rotation": "0",
            "quality": "native",
        }
        url = reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check etag exists
        self.assertIn("Etag", response, "Image should have an etag")

    def testImageCacheControl(self):
        client = Client()
        kwargs = {
            "datafile_id": self.datafile.id,
            "region": "full",
            "size": "full",
            "rotation": "0",
            "quality": "native",
        }
        url = reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check etag exists
        self.assertIn(
            "Cache-Control", response, "Image should have a Cache-Control header"
        )
        self.assertIn(
            "max-age",
            response["Cache-Control"],
            "Image should have a Cache-Control header",
        )
        # By default the image is public, so
        self.assertIn(
            "public",
            response["Cache-Control"],
            "Image should have a Cache-Control header",
        )

        is_logged_in = client.login(username="testuser", password="pwd")
        self.assertTrue(is_logged_in)

        experiment = self.datafile.dataset.get_first_experiment()
        experiment.public_access = Experiment.PUBLIC_ACCESS_NONE
        experiment.save()
        dataset = self.datafile.dataset
        dataset.public_access = Dataset.PUBLIC_ACCESS_NONE
        dataset.save()
        self.datafile.public_access = DataFile.PUBLIC_ACCESS_NONE
        self.datafile.save()

        url = reverse("tardis.tardis_portal.iiif.download_image", kwargs=kwargs)
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check etag exists
        self.assertIn(
            "Cache-Control", response, "Image should have a Cache-Control header"
        )
        self.assertIn(
            "max-age",
            response["Cache-Control"],
            "Image should have a Cache-Control header",
        )
        # By default the image is now private, so
        self.assertIn(
            "private",
            response["Cache-Control"],
            "Image should have a Cache-Control header",
        )
