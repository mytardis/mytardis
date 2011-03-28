#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE7
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
test_filters.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>

"""
from django.test import TestCase
from nose.plugins.skip import SkipTest


class ExifFilterTestCase(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        user = 'tardis_user1'
        pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

    def test_metadata_extraction(self):
        from os import path
        import datetime
        from fractions import Fraction
        try:
            from tardis.tardis_portal.filters.exif import EXIFFilter
        except:
            raise SkipTest()
        f = EXIFFilter("EXIF", "http://exif.schema")
        filename = path.join(path.abspath(path.dirname(__file__)), 'test.jpg')
        metadata = {'Exif.Thumbnail.ResolutionUnit': 2,
                    'Exif.Photo.ColorSpace': 65535,
                    'Exif.Image.Orientation': 1,
                    'Exif.Photo.PixelYDimension': 768L,
                    'Exif.Image.XResolution': Fraction(72, 1),
                    'Exif.Photo.PixelXDimension': 978L,
                    'Exif.Image.ExifTag': 164L,
                    'Exif.Thumbnail.Compression': 6,
                    'Exif.Image.DateTime': datetime.datetime(2005, 7, 8,
                                                             19, 17, 44),
                    'Exif.Image.YResolution': Fraction(72, 1),
                    'Exif.Image.ResolutionUnit': 2,
                    'Exif.Thumbnail.YResolution': Fraction(72, 1),
                    'Exif.Thumbnail.XResolution': Fraction(72, 1),
                    'Exif.Image.Software': 'Adobe Photoshop Elements 2.0'}
        self.assertEqual(f.getExif(filename), metadata)

    def test_parameter_filters(self):
        from os import path
        import datetime
        from fractions import Fraction
        try:
            from tardis.tardis_portal.filters.exif import EXIFFilter
        except:
            raise SkipTest()

        metadata = {'Exif.Thumbnail.ResolutionUnit': 2,
                    'Exif.Photo.ColorSpace': 65535,
                    'Exif.Image.Orientation': 1,
                    'Exif.Photo.PixelYDimension': 768L,
                    'Exif.Image.XResolution': Fraction(72, 1),
                    'Exif.Photo.PixelXDimension': 978L,
                    'Exif.Image.ExifTag': 164L,
                    'Exif.Thumbnail.Compression': 6,
                    'Exif.Image.DateTime': datetime.datetime(2005, 7, 8,
                                                             19, 17, 44),
                    'Exif.Image.YResolution': Fraction(72, 1),
                    'Exif.Image.ResolutionUnit': 2,
                    'Exif.Thumbnail.YResolution': Fraction(72, 1),
                    'Exif.Thumbnail.XResolution': Fraction(72, 1),
                    'Exif.Image.Software': 'Adobe Photoshop Elements 2.0'}

        f = EXIFFilter("EXIF", "http://exif.schema",
                       tagsToFind=["Exif.Photo.ColorSpace",
                                   'Exif.Image.Orientation'])
        s = f.getSchema()
        self.assertEqual(len(f.getParamaters(s, metadata)), 2)

        f = EXIFFilter("EXIF", "http://exif.schema",
                       tagsToExclude=["Exif.Photo.ColorSpace",
                                      'Exif.Image.Orientation'])
        s = f.getSchema()
        self.assertEqual(len(f.getParamaters(s, metadata)), 12)

    def test_create_schema(self):
        try:
            from tardis.tardis_portal.filters.exif import EXIFFilter
        except:
            raise SkipTest()

        f = EXIFFilter("EXIF", "http://exif.schema")
        self.assertEqual(str(f.getSchema()),
                         "Datafile schema: http://exif.schema")

    def test_update_schema(self):
        from os import path
        try:
            from tardis.tardis_portal.filters.exif import EXIFFilter
        except:
            raise SkipTest()

        f = EXIFFilter("EXIF", "http://exif.schema")
        filename = path.join(path.abspath(path.dirname(__file__)), 'test.jpg')
        self.assertEqual(len(f.getParamaters(f.getSchema(),
                                             f.getExif(filename))),
                         14)

    def test_save_metadata(self):
        from os import path
        try:
            from tardis.tardis_portal.filters.exif import EXIFFilter
        except:
            raise SkipTest()

        from tardis.tardis_portal import models

        filename = path.join(path.abspath(path.dirname(__file__)), 'test.jpg')

        exp = models.Experiment(title='test exp1',
                                institution_name='monash',
                                approved=True,
                                created_by=self.user,
                                public=False)
        exp.save()

        dataset = models.Dataset(description="dataset description...",
                                 experiment=exp)
        dataset.save()
        df_file = models.Dataset_File(dataset=dataset,
                                      filename='file1.txt',
                                      url=filename,
                                      protocol='')
        df_file.save()

        f = EXIFFilter("EXIF", "http://exif.schema")

        metadata = f.getExif(filename)
        parameters = f.getParamaters(f.getSchema(), metadata)
        ps = f.saveExifMetadata(df_file, f.getSchema(), metadata)
        self.assertEqual(len(ps.datafileparameter_set.all()), 14)
