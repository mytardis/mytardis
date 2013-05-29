'''
Testing the tastypie-based mytardis api

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
'''
import json

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User

from django.test.client import Client
from django.test import TestCase

from tastypie.test import ResourceTestCase

from tardis.tardis_portal.auth.authservice import AuthService
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.models import ExperimentACL
from tardis.tardis_portal.models.datafile import Dataset_File
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import ExperimentParameter
from tardis.tardis_portal.models.parameters import ExperimentParameterSet
from tardis.tardis_portal.models.parameters import ParameterName
from tardis.tardis_portal.models.parameters import Schema
from tardis.tardis_portal.models.replica import Replica


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
            Permission.objects.get(codename='add_dataset_file'))
        self.testexp = Experiment(title="test exp")
        self.testexp.approved = True
        self.testexp.created_by = self.user
        self.testexp.locked = False
        self.testexp.save()
        testacl = ExperimentACL(
            experiment=self.testexp,
            pluginId=django_user,
            entityId=str(self.user.id),
            canRead=True,
            canWrite=True,
            canDelete=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED)
        testacl.save()

    def get_credentials(self):
        return self.create_basic(username=self.username,
                                 password=self.password)


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


class Dataset_FileResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(Dataset_FileResourceTest, self).setUp()
        self.django_client = Client()
        self.django_client.login(username=self.username,
                                 password=self.password)
        testds = Dataset()
        testds.description = "test dataset"
        testds.save()
        testds.experiments.add(self.testexp)
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

        import tempfile
        post_file = tempfile.TemporaryFile()
        file_content = "123test\n"
        post_file.write(file_content)
        post_file.flush()
        post_file.seek(0)
        datafile_count = Dataset_File.objects.count()
        replica_count = Replica.objects.count()
        self.assertHttpCreated(self.django_client.post(
            '/api/v1/dataset_file/',
            data={post_data: "", "attached_file": post_file}))
        self.assertEqual(datafile_count + 1, Dataset_File.objects.count())
        self.assertEqual(replica_count + 1, Replica.objects.count())
        # fake-verify Replica, so we can access the file:
        newrep = Replica.objects.order_by('-pk')[0]
        newrep.verified = True
        newrep.save()
        new_file = Dataset_File.objects.order_by('-pk')[0]
        self.assertEqual(file_content, new_file.get_file().read())

    def test_shared_fs_single_file(self):
        pass


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
