'''
Testing the tastypie-based mytardis api

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
'''
import json
import os
import tempfile
import urllib

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from django.test.client import Client
from django.test import TestCase

from tastypie.test import ResourceTestCaseMixin

from tardis.tardis_portal.auth.authservice import AuthService
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.models import ObjectACL
from tardis.tardis_portal.models import UserProfile
from tardis.tardis_portal.models.datafile import DataFile, DataFileObject
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import ExperimentParameter
from tardis.tardis_portal.models.parameters import ExperimentParameterSet
from tardis.tardis_portal.models.parameters import ParameterName
from tardis.tardis_portal.models.parameters import Schema
from tardis.tardis_portal.models.facility import Facility
from tardis.tardis_portal.models.instrument import Instrument


class SerializerTest(TestCase):
    def test_pretty_serializer(self):
        from tardis.tardis_portal.api import PrettyJSONSerializer
        test_serializer = PrettyJSONSerializer()
        test_data = {"ugly": "json data",
                     "reformatted": 2,
                     "be": ["pretty", "and", "indented"]}
        test_output = test_serializer.to_json(test_data)
        ref_output = u'{\n  "be": [\n    "pretty", \n    "and", \n' +\
                     u'    "indented"\n  ], \n  "reformatted": 2, \n' +\
                     u'  "ugly": "json data"\n}\n'
        self.assertEqual(test_output, ref_output)

    def test_debug_serializer(self):
        with self.settings(DEBUG=False):
            import tardis.tardis_portal.api
            reload(tardis.tardis_portal.api)
            self.assertEqual(
                type(tardis.tardis_portal.api.default_serializer).__name__,
                'Serializer')
        with self.settings(DEBUG=True):
            reload(tardis.tardis_portal.api)
            self.assertEqual(
                type(tardis.tardis_portal.api.default_serializer).__name__,
                'PrettyJSONSerializer')


class ACLAuthorizationTest(TestCase):
    pass


class MyTardisResourceTestCase(ResourceTestCaseMixin, TestCase):
    '''
    abstract class without tests to combine common settings in one place
    '''
    def setUp(self):
        super(MyTardisResourceTestCase, self).setUp()
        self.username = 'mytardis'
        self.password = 'mytardis'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        test_auth_service = AuthService()
        test_auth_service._set_user_from_dict(
            self.user,
            user_dict={'first_name': 'Testing',
                       'last_name': 'MyTardis API',
                       'email': 'api_test@mytardis.org'},
            auth_method="None")
        self.user.user_permissions.add(
            Permission.objects.get(codename='change_dataset'))
        self.user.user_permissions.add(
            Permission.objects.get(codename='add_datafile'))
        self.user.user_permissions.add(
            Permission.objects.get(codename='add_instrument'))
        self.user.user_permissions.add(
            Permission.objects.get(codename='change_instrument'))
        self.user_profile = self.user.userprofile
        self.testgroup = Group(name="Test Group")
        self.testgroup.save()
        self.testgroup.user_set.add(self.user)
        self.testfacility = Facility(name="Test Facility",
                                     manager_group=self.testgroup)
        self.testfacility.save()
        self.testinstrument = Instrument(name="Test Instrument",
                                         facility=self.testfacility)
        self.testinstrument.save()
        self.testexp = Experiment(title="test exp")
        self.testexp.approved = True
        self.testexp.created_by = self.user
        self.testexp.locked = False
        self.testexp.save()
        testacl = ObjectACL(
            content_type=self.testexp.get_ct(),
            object_id=self.testexp.id,
            pluginId=django_user,
            entityId=str(self.user.id),
            canRead=True,
            canWrite=True,
            canDelete=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED)
        testacl.save()

    def get_credentials(self):
        return self.create_basic(username=self.username,
                                 password=self.password)

    def get_apikey_credentials(self):
        return self.create_apikey(username=self.username,
                                  api_key=self.user.api_key.key)


class MyTardisAuthenticationTest(MyTardisResourceTestCase):
    def test_bad_credentials(self):
        self.assertHttpOK(self.api_client.get(
            '/api/v1/experiment/'))
        good_credentials = self.create_basic(username=self.username,
                                             password=self.password)
        bad_credentials = self.create_basic(username=self.username,
                                            password="wrong pw, dude!")
        self.assertHttpOK(self.api_client.get(
            '/api/v1/experiment/',
            authentication=good_credentials))
        self.assertHttpUnauthorized(self.api_client.get(
            '/api/v1/experiment/',
            authentication=bad_credentials))

    def test_apikey_authentication(self):
        good_credentials = self.get_apikey_credentials()
        bad_credentials = self.create_apikey(username=self.username,
                                             api_key="wrong api_key")
        # Test api_key authentication
        self.assertHttpOK(self.api_client.get(
            '/api/v1/experiment/',
            authentication=good_credentials))
        self.assertHttpUnauthorized(self.api_client.get(
            '/api/v1/experiment/',
            authentication=bad_credentials))


class SchemaResourceTest(MyTardisResourceTestCase):
    pass


class ExperimentParameterSetResourceTest(MyTardisResourceTestCase):
    pass


class ExperimentParameterResourceTest(MyTardisResourceTestCase):
    pass


class ExperimentResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(ExperimentResourceTest, self).setUp()
        df_schema_name = "http://experi-mental.com/"
        self.test_schema = Schema(namespace=df_schema_name,
                                  type=Schema.EXPERIMENT)
        self.test_schema.save()
        self.test_parname1 = ParameterName(schema=self.test_schema,
                                           name="expparameter1",
                                           data_type=ParameterName.STRING)
        self.test_parname1.save()
        self.test_parname2 = ParameterName(schema=self.test_schema,
                                           name="expparameter2",
                                           data_type=ParameterName.NUMERIC)
        self.test_parname2.save()

    def test_post_experiment(self):
        schema_id = Schema.objects.first().id
        parm_id = ParameterName.objects.first().id
        post_data = {
            "description": "test description",
            "institution_name": "Monash University",
            "parameter_sets": [
                {
                    "schema": "http://experi-mental.com/",
                    "parameters": [
                        {
                            "name": "/api/v1/parametername/%d/" % parm_id,
                            "string_value": "Test16"
                        },
                        {
                            "name": "/api/v1/parametername/%d/" % (parm_id + 1),
                            "numerical_value": "244"
                        }
                    ]
                },
                {
                    "schema": "/api/v1/schema/%d/" % schema_id,
                    "parameters": [
                        {
                            "name": "expparameter1",
                            "string_value": "Test16"
                        },
                        {
                            "name": "expparameter2",
                            "value": "51244"
                        }
                    ]
                }
            ],
            "title": "testing parset creation2"
        }
        experiment_count = Experiment.objects.count()
        parameterset_count = ExperimentParameterSet.objects.count()
        parameter_count = ExperimentParameter.objects.count()
        self.assertHttpCreated(self.api_client.post(
            '/api/v1/experiment/',
            data=post_data,
            authentication=self.get_credentials()))
        self.assertEqual(experiment_count + 1, Experiment.objects.count())
        self.assertEqual(parameterset_count + 2,
                         ExperimentParameterSet.objects.count())
        self.assertEqual(parameter_count + 4,
                         ExperimentParameter.objects.count())

    def test_get_experiment(self):
        exp_id = Experiment.objects.first().id
        user_id = User.objects.first().id
        expected_output = {
            "approved": True,
            "created_by": "/api/v1/user/%d/" % user_id,
            "created_time": "2013-05-29T13:00:26.626580",
            "description": "",
            "end_time": None,
            "handle": None,
            "id": exp_id,
            "institution_name": "Monash University",
            "locked": False,
            "parameter_sets": [],
            "public_access": 1,
            "resource_uri": "/api/v1/experiment/%d/" % exp_id,
            "start_time": None,
            "title": "test exp",
            "update_time": "2013-05-29T13:00:26.626609",
            "url": None
        }
        output = self.api_client.get('/api/v1/experiment/%d/' % exp_id,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_data)
            if not key.endswith("_time"):
                self.assertEqual(returned_data[key], value)


class DatasetParameterSetResourceTest(MyTardisResourceTestCase):
    pass


class DatasetParameterResourceTest(MyTardisResourceTestCase):
    pass


class DatasetResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(DatasetResourceTest, self).setUp()
        self.extra_instrument = Instrument()
        self.extra_instrument = Instrument(name="Extra Instrument",
                                           facility=self.testfacility)
        self.extra_instrument.save()
        self.ds_no_instrument = Dataset()
        self.ds_no_instrument.description = "Dataset no instrument"
        self.ds_no_instrument.save()
        self.ds_no_instrument.experiments.add(self.testexp)
        self.ds_with_instrument = Dataset()
        self.ds_with_instrument.description = "Dataset with instrument"
        self.ds_with_instrument.instrument = self.testinstrument
        self.ds_with_instrument.save()
        self.ds_with_instrument.experiments.add(self.testexp)
        self.ds_with_instrument2 = Dataset()
        self.ds_with_instrument2.description = "Dataset with a different instrument"
        self.ds_with_instrument2.instrument = self.extra_instrument
        self.ds_with_instrument2.save()
        self.ds_with_instrument2.experiments.add(self.testexp)

    def test_get_dataset_no_instrument(self):
        uri = '/api/v1/dataset/?description=%s' \
            % urllib.quote(self.ds_no_instrument.description)
        output = self.api_client.get(uri,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        self.assertTrue('description' in returned_object)
        self.assertEqual(returned_object['description'],
                         self.ds_no_instrument.description)
        self.assertTrue('instrument' in returned_object)
        self.assertIsNone(returned_object['instrument'])

    def test_get_dataset_with_instrument(self):
        uri = '/api/v1/dataset/?description=%s' \
            % urllib.quote(self.ds_with_instrument.description)
        output = self.api_client.get(uri,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        self.assertTrue('description' in returned_object)
        self.assertEqual(returned_object['description'],
                         self.ds_with_instrument.description)
        self.assertTrue('instrument' in returned_object)
        self.assertTrue('id' in returned_object['instrument'])
        self.assertEqual(returned_object['instrument']['id'],
                         self.testinstrument.id)

    def test_get_dataset_filter_instrument(self):
        uri = '/api/v1/dataset/?instrument=%s' \
            % self.extra_instrument.id
        output = self.api_client.get(uri,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        self.assertTrue('instrument' in returned_object)
        self.assertTrue('id' in returned_object['instrument'])
        self.assertEqual(returned_object['instrument']['id'],
                         self.extra_instrument.id)

    def test_post_dataset(self):
        exp_id = Experiment.objects.first().id
        post_data = {
            "description": "api test dataset",
            "experiments": [
                "/api/v1/experiment/%d/" % exp_id,
            ],
            "immutable": False}
        dataset_count = Dataset.objects.count()
        self.assertHttpCreated(self.api_client.post(
            '/api/v1/dataset/',
            data=post_data,
            authentication=self.get_credentials()))
        self.assertEqual(dataset_count + 1, Dataset.objects.count())

class DataFileResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(DataFileResourceTest, self).setUp()
        self.django_client = Client()
        self.django_client.login(username=self.username,
                                 password=self.password)
        self.testds = Dataset()
        self.testds.description = "test dataset"
        self.testds.save()
        self.testds.experiments.add(self.testexp)
        df_schema_name = "http://datafileshop.com/"
        self.test_schema = Schema(namespace=df_schema_name,
                                  type=Schema.DATAFILE)
        self.test_schema.save()
        self.test_parname1 = ParameterName(schema=self.test_schema,
                                           name="fileparameter1",
                                           data_type=ParameterName.STRING)
        self.test_parname1.save()
        self.test_parname2 = ParameterName(schema=self.test_schema,
                                           name="fileparameter2",
                                           data_type=ParameterName.NUMERIC)
        self.test_parname2.save()

        self.datafile = DataFile(dataset=self.testds,
                                 filename="testfile.txt",
                                 size="42", md5sum='bogus')
        self.datafile.save()

    def test_post_single_file(self):
        ds_id = Dataset.objects.first().id
        post_data = """{
    "dataset": "/api/v1/dataset/%d/",
    "filename": "mytestfile.txt",
    "md5sum": "930e419034038dfad994f0d2e602146c",
    "size": "8",
    "mimetype": "text/plain",
    "parameter_sets": [{
        "schema": "http://datafileshop.com/",
        "parameters": [{
            "name": "fileparameter1",
            "value": "123"
        },
        {
            "name": "fileparameter2",
            "value": "123"
        }]
    }]
}""" % ds_id

        post_file = tempfile.NamedTemporaryFile()
        file_content = "123test\n"
        post_file.write(file_content)
        post_file.flush()
        post_file.seek(0)
        datafile_count = DataFile.objects.count()
        dfo_count = DataFileObject.objects.count()
        self.assertHttpCreated(self.django_client.post(
            '/api/v1/dataset_file/',
            data={"json_data": post_data, "attached_file": post_file}))
        self.assertEqual(datafile_count + 1, DataFile.objects.count())
        self.assertEqual(dfo_count + 1, DataFileObject.objects.count())
        new_file = DataFile.objects.order_by('-pk')[0]
        self.assertEqual(file_content, new_file.get_file().read())

    def test_shared_fs_single_file(self):
        pass

    def test_shared_fs_many_files(self):  # noqa # TODO too complex
        '''
        tests sending many files with known permanent location
        (useful for Australian Synchrotron ingestions)
        '''
        files = [{'content': 'test123\n'},
                 {'content': 'test246\n'}]
        from django.conf import settings
        for file_dict in files:
            post_file = tempfile.NamedTemporaryFile(
                dir=settings.DEFAULT_STORAGE_BASE_DIR)
            file_dict['filename'] = os.path.basename(post_file.name)
            file_dict['full_path'] = post_file.name
            post_file.write(file_dict['content'])
            post_file.flush()
            post_file.seek(0)
            file_dict['object'] = post_file

        def clumsily_build_uri(res_type, dataset):
            return '/api/v1/%s/%d/' % (res_type, dataset.id)

        def md5sum(filename):
            import hashlib
            md5 = hashlib.md5()
            with open(filename, 'rb') as f:
                for chunk in iter(lambda: f.read(128*md5.block_size), b''):
                    md5.update(chunk)
            return md5.hexdigest()

        def guess_mime(filename):
            import magic
            mime = magic.Magic(mime=True)
            return mime.from_file(filename)

        json_data = {"objects": []}
        for file_dict in files:
            file_json = {
                'dataset': clumsily_build_uri('dataset', self.testds),
                'filename': os.path.basename(file_dict['filename']),
                'md5sum': md5sum(file_dict['full_path']),
                'size': os.path.getsize(file_dict['full_path']),
                'mimetype': guess_mime(file_dict['full_path']),
                'replicas': [{
                    'url': file_dict['filename'],
                    'location': 'default',
                    'protocol': 'file',
                }],
            }
            json_data['objects'].append(file_json)

        datafile_count = DataFile.objects.count()
        dfo_count = DataFileObject.objects.count()
        self.assertHttpAccepted(self.api_client.patch(
            '/api/v1/dataset_file/',
            data=json_data,
            authentication=self.get_credentials()))
        self.assertEqual(datafile_count + 2, DataFile.objects.count())
        self.assertEqual(dfo_count + 2, DataFileObject.objects.count())
        # fake-verify DFO, so we can access the file:
        for newdfo in DataFileObject.objects.order_by('-pk')[0:2]:
            newdfo.verified = True
            newdfo.save()
        for sent_file, new_file in zip(
                reversed(files), DataFile.objects.order_by('-pk')[0:2]):
            self.assertEqual(sent_file['content'], new_file.get_file().read())

    def test_download_file(self):
        '''
        Doesn't actually check the content downloaded yet
        Just checks if the download API endpoint responds with 200
        '''
        output = self.api_client.get(
	    '/api/v1/dataset_file/%d/download/' % self.datafile.id,
            authentication=self.get_credentials())
        self.assertEqual(output.status_code, 200)


class DatafileParameterSetResourceTest(MyTardisResourceTestCase):
    pass


class DatafileParameterResourceTest(MyTardisResourceTestCase):
    pass


class LocationResourceTest(MyTardisResourceTestCase):
    pass


class ReplicaResourceTest(MyTardisResourceTestCase):
    pass


class GroupResourceTest(MyTardisResourceTestCase):

    def test_get_group_by_id(self):
        group_id = Group.objects.first().id
        expected_output = {
            "id": group_id,
            "name": "Test Group",
        }
        output = self.api_client.get('/api/v1/group/%d/' % group_id,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

    def test_get_group_by_name(self):
        group_id = Group.objects.first().id
        expected_output = {
            "id": group_id,
            "name": "Test Group",
        }
        output = self.api_client.get('/api/v1/group/%d/?name=%s' %
                          (group_id, urllib.quote(self.testgroup.name)),
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)


class FacilityResourceTest(MyTardisResourceTestCase):

    def test_get_facility_by_id(self):
        first_facility = Facility.objects.first().id
        first_group = Group.objects.first().id
        expected_output = {
            "id": first_facility,
            "manager_group": {
                "id": first_group,
                "name": "Test Group",
                "resource_uri": "/api/v1/group/%d/" % first_group
            },
            "name": "Test Facility",
            "resource_uri": "/api/v1/facility/%d/" % first_facility
        }
        output = self.api_client.get('/api/v1/facility/%d/' % first_facility,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

    def test_get_facility_by_name(self):
        first_facility = Facility.objects.first().id
        first_group = Group.objects.first().id
        expected_output = {
            "id": first_facility,
            "manager_group": {
                "id": first_group,
                "name": "Test Group",
                "resource_uri": "/api/v1/group/%d/" % first_group
            },
            "name": "Test Facility",
            "resource_uri": "/api/v1/facility/%d/" % first_facility
        }
        output = self.api_client.get('/api/v1/facility/?name=%s'
                                     % urllib.quote(self.testfacility.name),
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_object)
            self.assertEqual(returned_object[key], value)

    def test_get_facility_by_manager_group_id(self):
        """
        This type of query can be used to iterate through a user's groups,
        and use each group's id to determine which facilities a user
        manages, i.e. a way to obtain the functionality implemented by
          tardis.tardis_portal.models.facility.facilities_managed_by
        via the API
        """
        facility_id = Facility.objects.first().id
        group_id = Group.objects.first().id
        expected_output = {
            "manager_group": {
                "id": group_id,
                "name": "Test Group",
                "resource_uri": "/api/v1/group/%d/" % group_id
            },
            "id": facility_id,
            "name": "Test Facility",
            "resource_uri": "/api/v1/facility/%d/" % facility_id
        }
        output = self.api_client.get('/api/v1/facility/?manager_group__id=%d' %
                                     group_id,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_object)
            self.assertEqual(returned_object[key], value)


class InstrumentResourceTest(MyTardisResourceTestCase):

    def test_get_instrument_by_id(self):
        facility_id = Facility.objects.first().id
        group_id = Group.objects.first().id
        instrument_id = Instrument.objects.first().id
        expected_output = {
            "facility": {
                "manager_group": {
                    "id": group_id,
                    "name": "Test Group",
                    "resource_uri": "/api/v1/group/%d/" % group_id
                },
                "id": facility_id,
                "name": "Test Facility",
                "resource_uri": "/api/v1/facility/%d/" % facility_id
            },
            "id": instrument_id,
            "name": "Test Instrument",
            "resource_uri": "/api/v1/instrument/%d/" % instrument_id
        }
        output = self.api_client.get('/api/v1/instrument/%d/' %
                                     instrument_id,
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)

    def test_get_instrument_by_name(self):
        facility_id = Facility.objects.first().id
        group_id = Group.objects.first().id
        instrument_id = Instrument.objects.first().id
        expected_output = {
            "facility": {
                "manager_group": {
                    "id": group_id,
                    "name": "Test Group",
                    "resource_uri": "/api/v1/group/%d/" % group_id
                },
                "id": facility_id,
                "name": "Test Facility",
                "resource_uri": "/api/v1/facility/%d/" % facility_id
            },
            "id": instrument_id,
            "name": "Test Instrument",
            "resource_uri": "/api/v1/instrument/%d/" % instrument_id
        }
        output = self.api_client.get('/api/v1/instrument/?name=%s'
                                     % urllib.quote(self.testinstrument.name),
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        self.assertEqual(returned_data['meta']['total_count'], 1)
        returned_object = returned_data['objects'][0]
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_object)
            self.assertEqual(returned_object[key], value)

    def test_post_instrument(self):
        facility_id = Facility.objects.first().id
        post_data = {
            "name": "Another Test Instrument",
            "facility": "/api/v1/facility/%d/" % facility_id
        }
        instrument_count = Instrument.objects.count()
        self.assertHttpCreated(self.api_client.post(
            '/api/v1/instrument/',
            data=post_data,
            authentication=self.get_credentials()))
        self.assertEqual(instrument_count + 1, Instrument.objects.count())

    def test_rename_instrument(self):
        patch_data = {
            "name": "Renamed Test Instrument",
        }
        self.testinstrument.name = "Test Instrument"
        self.testinstrument.save()
        response = self.api_client.patch(
            '/api/v1/instrument/%d/' % self.testinstrument.id,
            data=patch_data,
            authentication=self.get_credentials())
        self.assertHttpAccepted(response)
        self.testinstrument = Instrument.objects.get(id=self.testinstrument.id)
        self.assertEqual(self.testinstrument.name,
                         "Renamed Test Instrument")
