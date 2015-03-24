'''
Testing the tastypie-based mytardis api

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
'''
import json
import os
import tempfile

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User

from django.test.client import Client
from django.test import TestCase

from tastypie.test import ResourceTestCase

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


class MyTardisResourceTestCase(ResourceTestCase):
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
        self.user_profile = UserProfile(user=self.user).save()
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
    def setUp(self):
        super(SchemaResourceTest, self).setUp()


class ExperimentParameterSetResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(ExperimentParameterSetResourceTest, self).setUp()


class ExperimentParameterResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(ExperimentParameterResourceTest, self).setUp()


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
        post_data = {
            "description": "test description",
            "institution_name": "Monash University",
            "parameter_sets": [
                {
                    "schema": "http://experi-mental.com/",
                    "parameters": [
                        {
                            "name": "/api/v1/parametername/1/",
                            "string_value": "Test16"
                        },
                        {
                            "name": "/api/v1/parametername/2/",
                            "numerical_value": "244"
                        }
                    ]
                },
                {
                    "schema": "/api/v1/schema/1/",
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
        expected_output = {
            "approved": True,
            "created_by": "/api/v1/user/1/",
            "created_time": "2013-05-29T13:00:26.626580",
            "description": "",
            "end_time": None,
            "handle": "",
            "id": 1,
            "institution_name": "Monash University",
            "locked": False,
            "parameter_sets": [],
            "public_access": 1,
            "resource_uri": "/api/v1/experiment/1/",
            "start_time": None,
            "title": "test exp",
            "update_time": "2013-05-29T13:00:26.626609",
            "url": None
        }
        output = self.api_client.get('/api/v1/experiment/1/',
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_data)
            if not key.endswith("_time"):
                self.assertEqual(returned_data[key], value)


class DatasetParameterSetResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(DatasetParameterSetResourceTest, self).setUp()


class DatasetParameterResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(DatasetParameterResourceTest, self).setUp()


class DatasetResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(DatasetResourceTest, self).setUp()


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

    def test_post_single_file(self):
        post_data = """{
    "dataset": "/api/v1/dataset/1/",
    "filename": "mytestfile.txt",
    "md5sum": "c858d6319609d6db3c091b09783c479c",
    "size": "12",
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
}"""

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
        # fake-verify DFO, so we can access the file:
        newdfo = DataFileObject.objects.order_by('-pk')[0]
        newdfo.verified = True
        newdfo.save()
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


class DatafileParameterSetResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(DatafileParameterSetResourceTest, self).setUp()


class DatafileParameterResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(DatafileParameterResourceTest, self).setUp()


class LocationResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(LocationResourceTest, self).setUp()


class ReplicaResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(ReplicaResourceTest, self).setUp()
