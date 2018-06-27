#
# Copyright (c) 2013, Centre for Microscopy and Microanalysis
#   (University of Queensland, Australia)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the University of Queensland nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from os import path

from django.test import TestCase
from django.db.models.signals import post_save
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.core.management import call_command
from django.http import HttpResponse

from tardis.tardis_portal.filters import FilterInitMiddleware
from tardis.tardis_portal.models import User, UserProfile, Experiment, \
    ObjectACL, Dataset, DataFile, DataFileObject, StorageBox

from tardis.tardis_portal.tests.test_download import get_size_and_sha512sum

TEST_FILTERS = [
    ('tardis.tardis_portal.tests.filters.test_middleware.Filter1',),
    ('tardis.tardis_portal.tests.filters.test_middleware.Filter2',),
]


class FilterInitTestCase(TestCase):
    def setUp(self):
        # Create test owner without enough details
        username, email, password = ('testuser',
                                     'testuser@example.test',
                                     'password')
        user = User.objects.create_user(username, email, password)

        # Create test experiment and make user the owner of it
        experiment = Experiment(title='Text Experiment',
                                institution_name='Test Uni',
                                created_by=user)
        experiment.save()
        acl = ObjectACL(
            pluginId='django_user',
            entityId=str(user.id),
            content_object=experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        acl.save()

        dataset = Dataset(description='dataset description...')
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()

        base_path = path.join(path.dirname(__file__), 'fixtures')
        s_box = StorageBox.get_default_storage(location=base_path)

        def create_datafile(index):
            testfile = path.join(base_path, 'middleware_test%d.txt' % index)

            size, sha512sum = get_size_and_sha512sum(testfile)

            datafile = DataFile(dataset=dataset,
                                filename=path.basename(testfile),
                                size=size,
                                sha512sum=sha512sum)
            datafile.save()
            dfo = DataFileObject(
                datafile=datafile,
                storage_box=s_box,
                uri=path.basename(testfile))
            dfo.save()

            if index != 1:
                dfo.verified = False
                dfo.save(update_fields=['verified'])
            return DataFile.objects.get(pk=datafile.pk)

        self.dataset = dataset
        self.datafiles = [create_datafile(i) for i in (1, 2)]

    def testFiltering(self):
        try:
            try:
                get_response = lambda _: HttpResponse('')
                FilterInitMiddleware(get_response, filters=TEST_FILTERS)
            except MiddlewareNotUsed:
                pass         # expected
            self.datafiles[0].save()
            t = Filter1.getTuples()
            self.assertEqual(len(t), 1)
            self.assertEqual(t[0][0], self.datafiles[0])
            self.assertIsNone(t[0][1])
            t = Filter2.getTuples()
            self.assertEqual(len(t), 1)
            self.assertEqual(t[0][0], self.datafiles[0])
            self.assertIsNone(t[0][1])

            self.datafiles[1].save()
            t = Filter1.getTuples()
            self.assertEqual(len(t), 0)
            t = Filter2.getTuples()
            self.assertEqual(len(t), 0)
            self.datafiles[0].file_objects.all()[0].save()
            t = Filter1.getTuples()
            self.assertEqual(len(t), 1)
            self.assertEqual(t[0][0], self.datafiles[0])
            self.assertTrue(t[0][1])
            t = Filter2.getTuples()
            self.assertEqual(len(t), 1)
            self.assertEqual(t[0][0], self.datafiles[0])
            self.assertTrue(t[0][1])

            self.datafiles[1].file_objects.all()[0].save(reverify=True)
            t = Filter1.getTuples()
            self.assertEqual(len(t), 1)
            t = Filter2.getTuples()
            self.assertEqual(len(t), 1)

        finally:
            # Remove our hooks!
            for f in TEST_FILTERS:
                post_save.disconnect(
                    sender=DataFile, dispatch_uid=f[0] + ".datafile")
                post_save.disconnect(
                    sender=DataFileObject, dispatch_uid=f[0] + ".dfo")



class RunFiltersTestCase(TestCase):

    def setUp(self):
        self.previous_post_save_filters = \
            getattr(settings, 'POST_SAVE_FILTERS', None)
        settings.POST_SAVE_FILTERS = TEST_FILTERS

    def tearDown(self):
        if self.previous_post_save_filters:
            settings.POST_SAVE_FILTERS = self.previous_post_save_filters

    def testList(self):
        '''
        Just test that we can run
        ./manage.py runfilters --list
        without any runtime exceptions
        '''
        call_command('runfilters', list=True)

    def testAll(self):
        '''
        Just test that we can run
        ./manage.py runfilters --all
        without any runtime exceptions
        '''
        call_command('runfilters', all=True)

    def testDryRun(self):
        '''
        Just test that we can run
        ./manage.py runfilters --dryRun
        without any runtime exceptions
        '''
        call_command('runfilters', dryRun=True)


class Filter1:
    tuples = []

    @classmethod
    def getTuples(cls):
        tuples = cls.tuples
        cls.tuples = []
        return tuples

    def __call__(self, sender, **kwargs):
        datafile = kwargs.get('instance')
        replica = kwargs.get('dfo')
        Filter1.tuples = Filter1.tuples + [(datafile, replica)]


class Filter2:
    tuples = []

    @classmethod
    def getTuples(cls):
        tuples = cls.tuples
        cls.tuples = []
        return tuples

    def __call__(self, sender, **kwargs):
        datafile = kwargs.get('instance')
        replica = kwargs.get('dfo')
        Filter2.tuples = Filter2.tuples + [(datafile, replica)]
