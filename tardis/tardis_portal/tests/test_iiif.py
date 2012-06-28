from lxml import etree
import json
import os
import tempfile

from compare import ensure, expect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.test import TestCase
from django.test.client import Client
from nose.plugins.skip import SkipTest

from tardis.tardis_portal.models import User, UserProfile, \
    Experiment, Dataset, Dataset_File, datafile

from tardis.tardis_portal.staging import write_uploaded_file_to_dataset
from tardis.tardis_portal.tests.test_download import get_size_and_sha512sum

from wand.image import Image

"""
Tests for IIIF API.

http://library.stanford.edu/iiif/image-api/

"""

def _create_datafile():
    user = User.objects.create_user('testuser', 'user@email.test', 'pwd')
    user.save()
    UserProfile(user=user).save()
    full_access = Experiment.PUBLIC_ACCESS_FULL
    experiment = Experiment.objects.create(title="IIIF Test",
                                           created_by=user,
                                           public_access=full_access)
    experiment.save()
    dataset = Dataset()
    dataset.save()
    dataset.experiments.add(experiment)
    dataset.save()

    # Create new Datafile
    tempfile = TemporaryUploadedFile('iiif_stored_file', None, None, None)
    with Image(filename='magick:rose') as img:
            img.format = 'tiff'
            img.save(file=tempfile.file)
            tempfile.file.flush()
    datafile = Dataset_File(dataset=dataset)
    datafile.size = os.path.getsize(tempfile.file.name)
    #os.remove(tempfilename)
    datafile.filename = 'iiif_named_file'
    datafile.url = write_uploaded_file_to_dataset(dataset, tempfile)
    datafile.verify(allowEmptyChecksums=True)
    datafile.save()
    return datafile


def _check_compliance_level(response):
    """
    Current complies with Level 1 API, so should assert no more.
    """
    import re
    ensure(re.search(r'\<http:\/\/library.stanford.edu\/iiif\/image-api\/'+\
                     r'compliance.html#level[01]\>;rel="compliesTo"',
                     response['Link']) != None,
           True,
           "Compliance header missing")


class Level0TestCase(TestCase):
    """ As per: http://library.stanford.edu/iiif/image-api/compliance.html """

    def setUp(self):
        self.datafile = _create_datafile()
        self.width = 70
        self.height = 46


    def testCanGetInfoAsXML(self):
        client = Client()
        kwargs = {'datafile_id': self.datafile.id,
                  'format': 'xml' }
        response = client.get(reverse('tardis.tardis_portal.iiif.download_info',
                                      kwargs=kwargs))
        expect(response.status_code).to_equal(200)
        # Check the response content is good
        nsmap = { 'i': 'http://library.stanford.edu/iiif/image-api/ns/' }
        xml = etree.fromstring(response.content)
        identifier = xml.xpath('/i:info/i:identifier', namespaces=nsmap)[0]
        expect(int(identifier.text)).to_equal(self.datafile.id)
        height = xml.xpath('/i:info/i:height', namespaces=nsmap)[0]
        expect(int(height.text)).to_equal(self.height)
        width = xml.xpath('/i:info/i:width', namespaces=nsmap)[0]
        expect(int(width.text)).to_equal(self.width)
        # Check compliance level
        _check_compliance_level(response)
        # Check etag exists
        ensure('Etag' in response, True, "Info should have an etag")


    def testCanGetInfoAsJSON(self):
        client = Client()
        kwargs = {'datafile_id': self.datafile.id,
                  'format': 'json' }
        response = client.get(reverse('tardis.tardis_portal.iiif.download_info',
                                      kwargs=kwargs))
        expect(response.status_code).to_equal(200)
        # Check the response content is good
        data = json.loads(response.content)
        expect(data['identifier']).to_equal(self.datafile.id)
        expect(data['height']).to_equal(self.height)
        expect(data['width']).to_equal(self.width)
        # Check compliance level
        _check_compliance_level(response)
        # Check etag exists
        ensure('Etag' in response, True, "Info should have an etag")

    def testCanGetOriginalImage(self):
        client = Client()
        kwargs = {'datafile_id': self.datafile.id,
                  'region': 'full',
                  'size': 'full',
                  'rotation': '0',
                  'quality': 'native' }
        response = client.get(reverse('tardis.tardis_portal.iiif.download_image',
                                      kwargs=kwargs))
        expect(response.status_code).to_equal(200)
        with Image(blob=response.content) as img:
            expect(img.format).to_equal('TIFF')
            expect(img.width).to_equal(self.width)
            expect(img.height).to_equal(self.height)
        # Check compliance level
        _check_compliance_level(response)
        # Check etag exists
        ensure('Etag' in response, True, "Image should have an etag")

class Level1TestCase(TestCase):
    """ As per: http://library.stanford.edu/iiif/image-api/compliance.html """

    def setUp(self):
        self.datafile = _create_datafile()
        self.width = 70
        self.height = 46

    def testCanGetJpegFormat(self):
        client = Client()
        kwargs = {'datafile_id': self.datafile.id,
                  'region': 'full',
                  'size': 'full',
                  'rotation': '0',
                  'quality': 'native',
                  'format': 'jpg' }
        response = client.get(reverse('tardis.tardis_portal.iiif.download_image',
                                      kwargs=kwargs))
        expect(response.status_code).to_equal(200)
        with Image(blob=response.content) as img:
            expect(img.format).to_equal('JPEG')
            expect(img.width).to_equal(self.width)
            expect(img.height).to_equal(self.height)
        # Check compliance level
        _check_compliance_level(response)

    def testHandleRegions(self):
        client = Client()
        # Inside box
        kwargs = {'datafile_id': self.datafile.id,
                  'region': '15,10,25,20',
                  'size': 'full',
                  'rotation': '0',
                  'quality': 'native',
                  'format': 'jpg' }
        response = client.get(reverse('tardis.tardis_portal.iiif.download_image',
                                      kwargs=kwargs))
        expect(response.status_code).to_equal(200)
        with Image(blob=response.content) as img:
            expect(img.width).to_equal(25)
            expect(img.height).to_equal(20)
        # Partly outside box
        kwargs = {'datafile_id': self.datafile.id,
                  'region': '60,41,20,20',
                  'size': 'full',
                  'rotation': '0',
                  'quality': 'native',
                  'format': 'jpg' }
        response = client.get(reverse('tardis.tardis_portal.iiif.download_image',
                                      kwargs=kwargs))
        expect(response.status_code).to_equal(200)
        with Image(blob=response.content) as img:
            expect(img.width).to_equal(10)
            expect(img.height).to_equal(5)
        # Check compliance level
        _check_compliance_level(response)

    def testHandleSizing(self):
        client = Client()
        def get_with_size(sizearg):
            kwargs = {'datafile_id': self.datafile.id,
                      'region': 'full',
                      'size': sizearg,
                      'rotation': '0',
                      'quality': 'native',
                      'format': 'jpg' }
            response = client.get(reverse('tardis.tardis_portal.iiif.download_image',
                                          kwargs=kwargs))
            expect(response.status_code).to_equal(200)
            return response

        permutations = [
                        # Width (aspect ratio preserved)
                        {'arg': '50,', 'width': 50, 'height': 33},
                        # Height (aspect ratio preserved)
                        {'arg': ',30', 'width': 46, 'height': 30},
                        # Percent size (aspect ratio preserved)
                        {'arg': 'pct:50', 'width': 35, 'height': 23},
                        ]
        for data in permutations:
            response = get_with_size(data['arg'])
            with Image(blob=response.content) as img:
                expect(img.width).to_equal(data['width'])
                expect(img.height).to_equal(data['height'])

    def testHandleRotation(self):
        client = Client()
        def get_with_rotation(rotation):
            kwargs = {'datafile_id': self.datafile.id,
                      'region': 'full',
                      'size': 'full',
                      'rotation': rotation,
                      'quality': 'native',
                      'format': 'jpg' }
            response = client.get(reverse('tardis.tardis_portal.iiif.download_image',
                                          kwargs=kwargs))
            expect(response.status_code).to_equal(200)
            return response

        rotations = [ get_with_rotation(i) for i in [0,90,180,270] ]
        for response in rotations[::2]:
            with Image(blob=response.content) as img:
                expect(img.width).to_equal(self.width)
                expect(img.height).to_equal(self.height)
        for response in rotations[1::2]:
            with Image(blob=response.content) as img:
                expect(img.width).to_equal(self.height)
                expect(img.height).to_equal(self.width)

class Level2TestCase(TestCase):
    """ As per: http://library.stanford.edu/iiif/image-api/compliance.html """

    def setUp(self):
        self.datafile = _create_datafile()
        self.width = 70
        self.height = 46

    def testCanGetRequiredFormats(self):
        client = Client()
        for ext, format in [('jpg', 'JPEG'), ('png', 'PNG'), ('jp2', 'JP2')]:
            kwargs = {'datafile_id': self.datafile.id,
                      'region': 'full',
                      'size': 'full',
                      'rotation': '0',
                      'quality': 'native',
                      'format': ext }
            response = client.get(reverse('tardis.tardis_portal.iiif.'+
                                          'download_image',
                                          kwargs=kwargs))
            expect(response.status_code).to_equal(200)
            with Image(blob=response.content) as img:
                expect(img.format).to_equal(format)
                expect(img.width).to_equal(self.width)
                expect(img.height).to_equal(self.height)
            # Check compliance level
            _check_compliance_level(response)

    def testHandleSizing(self):
        client = Client()
        def get_with_size(sizearg):
            kwargs = {'datafile_id': self.datafile.id,
                      'region': 'full',
                      'size': sizearg,
                      'rotation': '0',
                      'quality': 'native',
                      'format': 'jpg' }
            response = client.get(reverse('tardis.tardis_portal.iiif.download_image',
                                          kwargs=kwargs))
            expect(response.status_code).to_equal(200)
            return response

        permutations = [
                        # Exact dimensions *without* aspect ratio preserved
                        {'arg': '16,16', 'width': 16, 'height': 16},
                        # Maximum dimensions (aspect ratio preserved)
                        {'arg': '!16,16', 'width': 16, 'height': 11},
                        {'arg': '!90,11', 'width': 17, 'height': 11},
                        {'arg': '!16,10', 'width': 15, 'height': 10},
                        ]
        for data in permutations:
            response = get_with_size(data['arg'])
            with Image(blob=response.content) as img:
                expect(img.width).to_equal(data['width'])
                expect(img.height).to_equal(data['height'])

    def testCanGetRequiredQualities(self):
        client = Client()
        data = [('native', 3019), ('color', 3019), ('grey', 205), ('bitonal', 2)]
        # Not currently implemented
        raise SkipTest




