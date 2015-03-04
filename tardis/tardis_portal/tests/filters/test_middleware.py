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
from compare import expect

from django.test import TestCase
from django.db.models.signals import post_save
from django.core.exceptions import MiddlewareNotUsed

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
        profile = UserProfile(user=user, isDjangoAccount=True)
        profile.save()

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
                FilterInitMiddleware(filters=TEST_FILTERS)
            except MiddlewareNotUsed:
                pass         # expected
            self.datafiles[0].save()
            t = Filter1.getTuples()
            expect(len(t)).to_equal(1)
            expect(t[0][0]).to_equal(self.datafiles[0])
            expect(t[0][1]).to_be_none()
            t = Filter2.getTuples()
            expect(len(t)).to_equal(1)
            expect(t[0][0]).to_equal(self.datafiles[0])
            expect(t[0][1]).to_be_none()

            self.datafiles[1].save()
            t = Filter1.getTuples()
            expect(len(t)).to_equal(0)
            t = Filter2.getTuples()
            expect(len(t)).to_equal(0)

            self.datafiles[0].file_objects.all()[0].save()
            t = Filter1.getTuples()
            expect(len(t)).to_equal(2)
            expect(t[0][0]).to_equal(self.datafiles[0])
            expect(t[0][1]).to_be_truthy()
            t = Filter2.getTuples()
            expect(len(t)).to_equal(2)
            expect(t[0][0]).to_equal(self.datafiles[0])
            expect(t[0][1]).to_be_truthy()

            self.datafiles[1].file_objects.all()[0].save()
            t = Filter1.getTuples()
            # 2 because the missing md5 sum save runs the filter as well
            expect(len(t)).to_equal(2)
            t = Filter2.getTuples()
            expect(len(t)).to_equal(2)

        finally:
            # Remove our hooks!
            for f in TEST_FILTERS:
                post_save.disconnect(sender=DataFile, weak=False,
                                     dispatch_uid=f[0] + ".datafile")
                post_save.disconnect(sender=DataFileObject, weak=False,
                                     dispatch_uid=f[0] + ".dfo")


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
