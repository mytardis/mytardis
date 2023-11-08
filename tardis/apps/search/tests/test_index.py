import unittest
from io import StringIO

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.test import TestCase, override_settings
from django_elasticsearch_dsl.test import is_es_online
from django.utils import timezone

from tardis.apps.projects.models import (
    Project,
    ProjectParameter,
    ProjectParameterSet,
    ProjectACL,
)
from tardis.apps.search.documents import (
    DataFileDocument,
    DatasetDocument,
    ExperimentDocument,
    ProjectDocument,
)
from tardis.tardis_portal.models import (
    Schema,
    ParameterName,
    DataFile,
    Dataset,
    Experiment,
    Token,
    DatafileACL,
    DatasetACL,
    ExperimentACL,
    ExperimentParameterSet,
    ExperimentParameter,
    DatasetParameterSet,
    DatasetParameter,
    DatafileParameterSet,
    DatafileParameter,
)


"""
TODO improve these tests to include the following:
 - add parameter tests for all objects
   - test types of parameters index properly
 - test Indexing works for all object relations
"""


@unittest.skipUnless(is_es_online(), "Elasticsearch is offline")
@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class IndexTestCase(TestCase):
    def setUp(self):
        """
        Create a series of users (inc. public) to be used for various index tests.
        Create basic Proj/Exp/Set/File + created_by_user ACLs to be used in the tests.
        """
        publicuser = "public_user"
        pwd = "secret"
        publicemail = "public@test.com"
        self.publicuser = User.objects.create_user(publicuser, publicemail, pwd)
        user = "tardis_user1"
        pwd = "secret"
        email = ""
        self.user = User.objects.create_user(user, email, pwd)
        # user_grp will be added to a group, and should only see
        # search results for objects that the group has an ACL for
        user_grp = "tardis_user2"
        email_grp = "group@test.com"
        self.user_grp = User.objects.create_user(user_grp, email_grp, pwd)
        self.group = Group.objects.create(name="Group1")
        # user_token will be given a token_ACL, which are ignored in search for now.
        # This user shouldn't see any results (unless token functionality added to search)
        user_token = "tardis_user3"
        email_token = "token@test.com"
        self.user_token = User.objects.create_user(user_token, email_token, pwd)
        self.token = Token(user=self.user)
        self.token.save()

        self.out = StringIO()
        call_command("search_index", stdout=self.out, action="delete", force=True)

        # Create project object
        self.proj = Project(
            name="Test Project 1",
            description="This is a test.",
            principal_investigator=self.user,
            created_by=self.user,
        )
        self.proj.save()
        # Explicit user ACL creation for project
        acl = ProjectACL(
            user=self.user,
            project=self.proj,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
            canRead=True,
            canDownload=True,
            canSensitive=True,
        )
        acl.save()

        # create experiment object
        self.exp = Experiment(
            title="test exp1",
            institution_name="monash",
            description="Test Description",
            created_by=self.user,
        )
        self.exp.save()
        # Explicit user ACL creation for experiment
        acl = ExperimentACL(
            user=self.user,
            experiment=self.exp,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            canRead=True,
            canDownload=True,
            canSensitive=True,
        )
        acl.save()

        # add relation between Proj and Exp (required for all ACL modes)
        self.proj.experiments.add(self.exp)

        # create dataset object
        # dataset1 belongs to experiment1
        self.dataset = Dataset(description="test_dataset")
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()
        # Explicit user ACL creation for dataset
        acl = DatasetACL(
            user=self.user,
            dataset=self.dataset,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
            canRead=True,
            canDownload=True,
            canSensitive=True,
        )
        acl.save()

        # create datafile object
        settings.REQUIRE_DATAFILE_SIZES = False
        settings.REQUIRE_DATAFILE_CHECKSUMS = False
        self.datafile = DataFile(dataset=self.dataset, filename="test.txt")
        self.datafile.save()
        # Explicit user ACL creation for datafile
        acl = DatafileACL(
            user=self.user,
            datafile=self.datafile,
            aclOwnershipType=DatafileACL.OWNER_OWNED,
            canRead=True,
            canDownload=True,
            canSensitive=True,
        )
        acl.save()

    def test_create_index(self):
        """
        Test the existence of proj/exp/set/file document objects.
        """
        # search on project
        search = ProjectDocument.search()
        # query for title(exact matching)
        query = search.query("match", name="Test Project 1")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].name, "Test Project 1")

        # search on experiment
        search = ExperimentDocument.search()
        # query for title(exact matching)
        query = search.query("match", title="test exp1")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].title, "test exp1")

        # search on dataset
        search = DatasetDocument.search()
        query = search.query("match", description="test_dataset")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits.total.value, 1)

        # search on datafile
        search = DataFileDocument.search()
        query = search.query("match", filename="test.txt")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].filename, self.datafile.filename)

    def test_datafile_extension(self):
        """
        Test whether datafile extension fields are indexed properly.
        """
        # datafile with single extension (.txt) already exists as self.datafile
        datafile2 = DataFile(dataset=self.dataset, filename="test.tar.gz")
        datafile2.save()

        datafile3 = DataFile(dataset=self.dataset, filename="test_no_extension")
        datafile3.save()

        search = DataFileDocument.search()
        query = search.query("match", filename="test.txt")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits.total.value, 1)
        self.assertEqual(result.hits[0].file_extension, "txt")

        # gz alone should be indexed for tar.gz
        search = DataFileDocument.search()
        query = search.query("match", filename="test.tar.gz")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits.total.value, 1)
        self.assertEqual(result.hits[0].file_extension, "gz")

        search = DataFileDocument.search()
        query = search.query("match", filename="test_no_extension")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits.total.value, 1)
        self.assertEqual(result.hits[0].file_extension, "")

    def test_ACL_types(self):
        """
        Test that ACLs for users & groups are indexed, but that tokens are not.
        """
        # Explicit ACL creation for user+group+token for project
        acl = ProjectACL(
            group=self.group,
            project=self.proj,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
            canRead=True,
        )
        acl.save()
        acl = ProjectACL(
            token=self.token,
            project=self.proj,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
            canRead=True,
        )
        acl.save()
        # Explicit ACL creation for user+group+token for experiment
        acl = ExperimentACL(
            group=self.group,
            experiment=self.exp,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            canRead=True,
        )
        acl.save()
        acl = ExperimentACL(
            token=self.token,
            experiment=self.exp,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            canRead=True,
        )
        acl.save()
        # Explicit ACL creation for user+group+token for dataset
        acl = DatasetACL(
            group=self.group,
            dataset=self.dataset,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
            canRead=True,
        )
        acl.save()
        acl = DatasetACL(
            token=self.token,
            dataset=self.dataset,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
            canRead=True,
        )
        acl.save()
        # Explicit ACL creation for user+group+token for datafile
        acl = DatafileACL(
            group=self.group,
            datafile=self.datafile,
            aclOwnershipType=DatafileACL.OWNER_OWNED,
            canRead=True,
        )
        acl.save()
        acl = DatafileACL(
            token=self.token,
            datafile=self.datafile,
            aclOwnershipType=DatafileACL.OWNER_OWNED,
            canRead=True,
        )
        acl.save()

        correct_acl_structure = [
            {
                "pluginId": "django_user",
                "entityId": self.user.id,
                "canDownload": True,
                "canSensitive": True,
            },
            {
                "pluginId": "django_group",
                "entityId": self.group.id,
                "canDownload": False,
                "canSensitive": False,
            },
        ]

        # manually rebuild indexes to ensure they are up-to-date for these
        # tests (related_index triggers should be tested elsewhere)
        self.out = StringIO()
        call_command("search_index", stdout=self.out, action="rebuild", force=True)

        search = ProjectDocument.search()
        query = search.query("match", name="Test Project 1")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        search = ExperimentDocument.search()
        query = search.query("match", title="test exp1")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        search = DatasetDocument.search()
        query = search.query("match", description="test_dataset")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        search = DataFileDocument.search()
        query = search.query("match", filename="test.txt")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

    def test_parameter_indexing(self):
        """
        Test that parameters are properly indexed into proj/exp/set/file documents.
        Tests are for parameter types: string, numerical, datetime
        """
        # Create schemas
        schema_proj = Schema(
            namespace="http://test.namespace/proj/1",
            name="ProjSchema",
            type=Schema.PROJECT,
        )
        schema_proj.save()
        schema_exp = Schema(
            namespace="http://test.namespace/exp/1",
            name="ExpSchema",
            type=Schema.EXPERIMENT,
        )
        schema_exp.save()
        schema_set = Schema(
            namespace="http://test.namespace/set/1",
            name="SetSchema",
            type=Schema.DATASET,
        )
        schema_set.save()
        schema_file = Schema(
            namespace="http://test.namespace/file/1",
            name="FileSchema",
            type=Schema.DATAFILE,
        )
        schema_file.save()

        # define parameter types and names to test on
        param_types = [
            "STRING",
            "NUMERIC",
            "DATETIME",
            # "URL",
            # "LINK",
            # "FILENAME",
            # "LONGSTRING",
            # "JSON",
        ]

        param_names = {}
        # Create Numeric/string/datetime parameters for each
        # of the 4 schemas above
        for schema in [schema_proj, schema_exp, schema_set, schema_file]:
            param_names[schema.name] = {}
            for data_type_str in param_types:
                paramname = ParameterName(
                    schema=schema,
                    name=data_type_str,
                    full_name=data_type_str,
                    data_type=getattr(ParameterName, data_type_str),
                )
                if paramname.name == "DATETIME":
                    paramname.sensitive = True
                paramname.save()
                param_names[schema.name][data_type_str] = paramname
        # define a time for datetime parameters
        now = timezone.now()

        # Create project parameterset and parameters
        proj_parameterset = ProjectParameterSet(schema=schema_proj, project=self.proj)
        proj_parameterset.save()
        proj_param_string = ProjectParameter.objects.create(
            parameterset=proj_parameterset,
            name=param_names[schema_proj.name]["STRING"],
            string_value="stringtest",
        )
        proj_param_numeric = ProjectParameter.objects.create(
            parameterset=proj_parameterset,
            name=param_names[schema_proj.name]["NUMERIC"],
            numerical_value=123,
        )
        proj_param_datetime = ProjectParameter.objects.create(
            parameterset=proj_parameterset,
            name=param_names[schema_proj.name]["DATETIME"],
            datetime_value=now,
        )

        # Create experiment parameterset and parameters
        exp_parameterset = ExperimentParameterSet(
            schema=schema_exp, experiment=self.exp
        )
        exp_parameterset.save()
        exp_param_string = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=param_names[schema_exp.name]["STRING"],
            string_value="stringtest",
        )
        exp_param_numeric = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=param_names[schema_exp.name]["NUMERIC"],
            numerical_value=123,
        )
        exp_param_datetime = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=param_names[schema_exp.name]["DATETIME"],
            datetime_value=now,
        )

        # Create dataset parameterset and parameters
        set_parameterset = DatasetParameterSet(schema=schema_set, dataset=self.dataset)
        set_parameterset.save()
        set_param_string = DatasetParameter.objects.create(
            parameterset=set_parameterset,
            name=param_names[schema_set.name]["STRING"],
            string_value="stringtest",
        )
        set_param_numeric = DatasetParameter.objects.create(
            parameterset=set_parameterset,
            name=param_names[schema_set.name]["NUMERIC"],
            numerical_value=123,
        )
        set_param_datetime = DatasetParameter.objects.create(
            parameterset=set_parameterset,
            name=param_names[schema_set.name]["DATETIME"],
            datetime_value=now,
        )

        # Create datafile parameterset and parameters
        file_parameterset = DatafileParameterSet(
            schema=schema_file, datafile=self.datafile
        )
        file_parameterset.save()
        file_param_string = DatafileParameter.objects.create(
            parameterset=file_parameterset,
            name=param_names[schema_file.name]["STRING"],
            string_value="stringtest",
        )
        file_param_numeric = DatafileParameter.objects.create(
            parameterset=file_parameterset,
            name=param_names[schema_file.name]["NUMERIC"],
            numerical_value=123,
        )
        file_param_datetime = DatafileParameter.objects.create(
            parameterset=file_parameterset,
            name=param_names[schema_file.name]["DATETIME"],
            datetime_value=now,
        )

        # manually rebuild indexes to ensure they are up-to-date for these
        # tests (related_index triggers should be tested elsewhere)
        self.out = StringIO()
        call_command("search_index", stdout=self.out, action="rebuild", force=True)

        def param_struct(
            param_names, param_string, param_numeric, param_datetime, schema
        ):
            correct_param_structure = {
                "string": [
                    {
                        "pn_id": str(param_names[schema.name]["STRING"].id),
                        "pn_name": "STRING",
                        "sensitive": "False",
                        "value": param_string.string_value,
                    }
                ],
                "numeric": [
                    {
                        "pn_id": str(param_names[schema.name]["NUMERIC"].id),
                        "pn_name": "NUMERIC",
                        "sensitive": "False",
                        "value": param_numeric.numerical_value,
                    }
                ],
                "datetime": [
                    {
                        "pn_id": str(param_names[schema.name]["DATETIME"].id),
                        "pn_name": "DATETIME",
                        "sensitive": "True",
                        "value": param_datetime.datetime_value,
                    }
                ],
                "schemas": [{"schema_id": str(schema.id)}],
            }
            return correct_param_structure

        search = ProjectDocument.search()
        query = search.query("match", name="Test Project 1")
        result = query.execute(ignore_cache=True)
        correct_param_structure = param_struct(
            param_names,
            proj_param_string,
            proj_param_numeric,
            proj_param_datetime,
            schema_proj,
        )
        print(result.hits[0].parameters)
        print(correct_param_structure)
        print(result.hits[0].parameters.string)
        print(result.hits[0].parameters.numeric)
        print(result.hits[0].parameters.datetime)
        print(result.hits[0].parameters.schemas)
        print()
        self.assertEqual(result.hits[0].parameters, correct_param_structure)

        search = ExperimentDocument.search()
        query = search.query("match", title="test exp1")
        result = query.execute(ignore_cache=True)
        correct_param_structure = param_struct(
            param_names,
            exp_param_string,
            exp_param_numeric,
            exp_param_datetime,
            schema_exp,
        )
        print(result.hits[0].parameters)
        print(correct_param_structure)
        print()
        self.assertEqual(result.hits[0].acls, correct_param_structure)

        search = DatasetDocument.search()
        query = search.query("match", description="test_dataset")
        result = query.execute(ignore_cache=True)
        correct_param_structure = param_struct(
            param_names,
            set_param_string,
            set_param_numeric,
            set_param_datetime,
            schema_set,
        )
        print(result.hits[0].parameters)
        print(correct_param_structure)
        print()
        self.assertEqual(result.hits[0].acls, correct_param_structure)

        search = DataFileDocument.search()
        query = search.query("match", filename="test.txt")
        result = query.execute(ignore_cache=True)
        correct_param_structure = param_struct(
            param_names,
            file_param_string,
            file_param_numeric,
            file_param_datetime,
            schema_file,
        )
        print(result.hits[0].parameters)
        print(correct_param_structure)
        print()
        self.assertEqual(result.hits[0].acls, correct_param_structure)

    def tearDown(self):
        self.datafile.delete()
        self.dataset.delete()
        self.exp.delete()
        self.proj.delete()
        self.publicuser.delete()
        self.user.delete()
        self.user_grp.delete()
        self.user_token.delete()
