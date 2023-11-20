# pylint: disable=C0302
import unittest
from io import StringIO

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.db.models.signals import post_delete
from django.test import TestCase, override_settings
from django.utils import timezone
from django_elasticsearch_dsl.test import is_es_online

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
    update_es_relations,
    setup_sync_signals,
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
    Instrument,
    Facility,
)


"""
TODO improve these tests to include the following:
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

        # set up post_delete signals in these tests, disabled beyond search tests.
        setup_sync_signals()

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
        self.projacl = ProjectACL(
            user=self.user,
            project=self.proj,
            aclOwnershipType=ProjectACL.OWNER_OWNED,
            canRead=True,
            canDownload=True,
            canSensitive=True,
        )
        self.projacl.save()

        # create experiment object
        self.exp = Experiment(
            title="test exp1",
            institution_name="monash",
            description="Test Description",
            created_by=self.user,
        )
        self.exp.save()
        # Explicit user ACL creation for experiment
        self.expacl = ExperimentACL(
            user=self.user,
            experiment=self.exp,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            canRead=True,
            canDownload=True,
            canSensitive=True,
        )
        self.expacl.save()

        # add relation between Proj and Exp (required for all ACL modes)
        self.proj.experiments.add(self.exp)

        # create dataset object
        # dataset1 belongs to experiment1
        self.dataset = Dataset(description="test_dataset")
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()
        # Explicit user ACL creation for dataset
        self.setacl = DatasetACL(
            user=self.user,
            dataset=self.dataset,
            aclOwnershipType=DatasetACL.OWNER_OWNED,
            canRead=True,
            canDownload=True,
            canSensitive=True,
        )
        self.setacl.save()

        # create datafile object
        settings.REQUIRE_DATAFILE_SIZES = False
        settings.REQUIRE_DATAFILE_CHECKSUMS = False
        self.datafile = DataFile(dataset=self.dataset, filename="test.txt")
        self.datafile.save()
        # Explicit user ACL creation for datafile
        self.fileacl = DatafileACL(
            user=self.user,
            datafile=self.datafile,
            aclOwnershipType=DatafileACL.OWNER_OWNED,
            canRead=True,
            canDownload=True,
            canSensitive=True,
        )
        self.fileacl.save()

        # Create schemas
        self.schema_proj = Schema(
            namespace="http://test.namespace/proj/1",
            name="ProjSchema",
            type=Schema.PROJECT,
        )
        self.schema_proj.save()
        self.schema_exp = Schema(
            namespace="http://test.namespace/exp/1",
            name="ExpSchema",
            type=Schema.EXPERIMENT,
        )
        self.schema_exp.save()
        self.schema_set = Schema(
            namespace="http://test.namespace/set/1",
            name="SetSchema",
            type=Schema.DATASET,
        )
        self.schema_set.save()
        self.schema_file = Schema(
            namespace="http://test.namespace/file/1",
            name="FileSchema",
            type=Schema.DATAFILE,
        )
        self.schema_file.save()

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
        for schema in [
            self.schema_proj,
            self.schema_exp,
            self.schema_set,
            self.schema_file,
        ]:
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
        proj_parameterset = ProjectParameterSet(
            schema=self.schema_proj, project=self.proj
        )
        proj_parameterset.save()
        proj_param_string = ProjectParameter.objects.create(
            parameterset=proj_parameterset,
            name=param_names[self.schema_proj.name]["STRING"],
            string_value="stringtest",
        )
        proj_param_numeric = ProjectParameter.objects.create(
            parameterset=proj_parameterset,
            name=param_names[self.schema_proj.name]["NUMERIC"],
            numerical_value=123.0,
        )

        proj_param_datetime = ProjectParameter.objects.create(
            parameterset=proj_parameterset,
            name=param_names[self.schema_proj.name]["DATETIME"],
            datetime_value=now,
        )

        # Create experiment parameterset and parameters
        exp_parameterset = ExperimentParameterSet(
            schema=self.schema_exp, experiment=self.exp
        )
        exp_parameterset.save()
        exp_param_string = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=param_names[self.schema_exp.name]["STRING"],
            string_value="stringtest",
        )
        exp_param_numeric = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=param_names[self.schema_exp.name]["NUMERIC"],
            numerical_value=123.0,
        )

        exp_param_datetime = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=param_names[self.schema_exp.name]["DATETIME"],
            datetime_value=now,
        )

        # Create dataset parameterset and parameters
        set_parameterset = DatasetParameterSet(
            schema=self.schema_set, dataset=self.dataset
        )
        set_parameterset.save()
        set_param_string = DatasetParameter.objects.create(
            parameterset=set_parameterset,
            name=param_names[self.schema_set.name]["STRING"],
            string_value="stringtest",
        )
        set_param_numeric = DatasetParameter.objects.create(
            parameterset=set_parameterset,
            name=param_names[self.schema_set.name]["NUMERIC"],
            numerical_value=123.0,
        )

        set_param_datetime = DatasetParameter.objects.create(
            parameterset=set_parameterset,
            name=param_names[self.schema_set.name]["DATETIME"],
            datetime_value=now,
        )

        # Create datafile parameterset and parameters
        file_parameterset = DatafileParameterSet(
            schema=self.schema_file, datafile=self.datafile
        )
        file_parameterset.save()
        file_param_string = DatafileParameter.objects.create(
            parameterset=file_parameterset,
            name=param_names[self.schema_file.name]["STRING"],
            string_value="stringtest",
        )
        file_param_numeric = DatafileParameter.objects.create(
            parameterset=file_parameterset,
            name=param_names[self.schema_file.name]["NUMERIC"],
            numerical_value=123.0,
        )
        file_param_datetime = DatafileParameter.objects.create(
            parameterset=file_parameterset,
            name=param_names[self.schema_file.name]["DATETIME"],
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
                        "sensitive": False,
                        "value": param_string.string_value,
                    }
                ],
                "numerical": [
                    {
                        "pn_id": str(param_names[schema.name]["NUMERIC"].id),
                        "pn_name": "NUMERIC",
                        "sensitive": False,
                        "value": param_numeric.numerical_value,
                    }
                ],
                "datetime": [
                    {
                        "pn_id": str(param_names[schema.name]["DATETIME"].id),
                        "pn_name": "DATETIME",
                        "sensitive": True,
                        "value": str(param_datetime.datetime_value).replace(" ", "T"),
                    }
                ],
                "schemas": [{"schema_id": schema.id}],
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
            self.schema_proj,
        )
        result.to_dict()
        result_params = result["hits"]["hits"][0]["_source"]["parameters"]
        self.assertEqual(result_params.string, correct_param_structure["string"])
        self.assertEqual(result_params.numerical, correct_param_structure["numerical"])
        self.assertEqual(result_params.datetime, correct_param_structure["datetime"])
        self.assertEqual(result_params.schemas, correct_param_structure["schemas"])

        search = ExperimentDocument.search()
        query = search.query("match", title="test exp1")
        result = query.execute(ignore_cache=True)
        correct_param_structure = param_struct(
            param_names,
            exp_param_string,
            exp_param_numeric,
            exp_param_datetime,
            self.schema_exp,
        )
        result.to_dict()
        result_params = result["hits"]["hits"][0]["_source"]["parameters"]
        self.assertEqual(result_params.string, correct_param_structure["string"])
        self.assertEqual(result_params.numerical, correct_param_structure["numerical"])
        self.assertEqual(result_params.datetime, correct_param_structure["datetime"])
        self.assertEqual(result_params.schemas, correct_param_structure["schemas"])

        search = DatasetDocument.search()
        query = search.query("match", description="test_dataset")
        result = query.execute(ignore_cache=True)
        correct_param_structure = param_struct(
            param_names,
            set_param_string,
            set_param_numeric,
            set_param_datetime,
            self.schema_set,
        )
        result.to_dict()
        result_params = result["hits"]["hits"][0]["_source"]["parameters"]
        self.assertEqual(result_params.string, correct_param_structure["string"])
        self.assertEqual(result_params.numerical, correct_param_structure["numerical"])
        self.assertEqual(result_params.datetime, correct_param_structure["datetime"])
        self.assertEqual(result_params.schemas, correct_param_structure["schemas"])

        search = DataFileDocument.search()
        query = search.query("match", filename="test.txt")
        result = query.execute(ignore_cache=True)
        correct_param_structure = param_struct(
            param_names,
            file_param_string,
            file_param_numeric,
            file_param_datetime,
            self.schema_file,
        )
        result.to_dict()
        result_params = result["hits"]["hits"][0]["_source"]["parameters"]
        self.assertEqual(result_params.string, correct_param_structure["string"])
        self.assertEqual(result_params.numerical, correct_param_structure["numerical"])
        self.assertEqual(result_params.datetime, correct_param_structure["datetime"])
        self.assertEqual(result_params.schemas, correct_param_structure["schemas"])

    def test_project_get_instances_from_related(self):
        """
        Test that related instances trigger a project reindex.
        """
        # Update username
        self.user.username = "newusername"
        self.user.save()
        # create search and query objects once
        search = ProjectDocument.search()
        query = search.query("match", name="Test Project 1")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].principal_investigator.username, "newusername")

        # Update relevant ACL models and perms
        correct_acl_structure = [
            {
                "pluginId": "django_user",
                "entityId": self.user.id,
                "canDownload": False,
                "canSensitive": False,
            }
        ]
        if settings.ONLY_EXPERIMENT_ACLS:
            # Update related experiment ACL perms
            self.expacl.canSensitive = False
            self.expacl.canDownload = False
            self.expacl.save()
        else:
            # Update project ACL perms
            self.projacl.canSensitive = False
            self.projacl.canDownload = False
            self.projacl.save()
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        # test deletion of ACLs
        if settings.ONLY_EXPERIMENT_ACLS:
            self.expacl.delete()
        else:
            self.projacl.delete()
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, [])

        # test creation of new ACL
        if settings.ONLY_EXPERIMENT_ACLS:
            newacl = ExperimentACL(
                user=self.user,
                experiment=self.exp,
                aclOwnershipType=ExperimentACL.OWNER_OWNED,
                canRead=True,
            )
        else:
            newacl = ProjectACL(
                user=self.user,
                project=self.proj,
                aclOwnershipType=ProjectACL.OWNER_OWNED,
                canRead=True,
            )
        newacl.save()
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        # test that public flag updated by experiments in Macro-mode
        if settings.ONLY_EXPERIMENT_ACLS:
            # Update existing parent experiment to have public=embargoed/25
            self.exp.public_access = Experiment.PUBLIC_ACCESS_EMBARGO
            self.exp.save()
            result = query.execute(ignore_cache=True)
            self.assertEqual(result.hits[0].public_access, 25)
            # add new experiment as parent with full public access/100
            # create experiment object
            exp_public = Experiment(
                title="public exp",
                institution_name="monash",
                description="Test Description",
                created_by=self.user,
                public_access=Experiment.PUBLIC_ACCESS_FULL,
            )
            exp_public.save()
            self.proj.experiments.add(exp_public)
            result = query.execute(ignore_cache=True)
            self.assertEqual(result.hits[0].public_access, 100)
            # Now test that deleting public exp reverts flag
            # TODO deletion doesn't work syncronously
            # exp_public.delete()
            # result = query.execute(ignore_cache=True)
            # self.assertEqual(result.hits[0].public_access, 25)

        # test creation of parameterset and schema
        paramname = ParameterName(
            schema=self.schema_proj,
            name="test_param",
            full_name="Test Parameter",
            data_type=getattr(ParameterName, "STRING"),
        )
        paramname.save()
        proj_parameterset = ProjectParameterSet(
            schema=self.schema_proj, project=self.proj
        )
        proj_parameterset.save()
        result = query.execute(ignore_cache=True)
        result.to_dict()
        result_params = result["hits"]["hits"][0]["_source"]["parameters"]
        # schema ID should be present
        self.assertEqual(result_params.schemas, [{"schema_id": self.schema_proj.id}])
        # Parameters should be empty
        self.assertEqual(result_params.string, [])
        # test creation of parameter
        proj_param = ProjectParameter.objects.create(
            parameterset=proj_parameterset,
            name=paramname,
            string_value="stringtest",
        )
        result = query.execute(ignore_cache=True)
        result.to_dict()
        result_params = result["hits"]["hits"][0]["_source"]["parameters"]
        # Parameter should be present
        self.assertEqual(
            result_params.string,
            [
                {
                    "pn_id": str(paramname.id),
                    "pn_name": paramname.full_name,
                    "sensitive": False,
                    "value": proj_param.string_value,
                }
            ],
        )

        # test delete of param
        proj_param.delete()
        result = query.execute(ignore_cache=True)
        result.to_dict()
        result_params = result["hits"]["hits"][0]["_source"]["parameters"]
        self.assertEqual(result_params.string, [])
        # test delete of paramset
        proj_parameterset.delete()
        result = query.execute(ignore_cache=True)
        result.to_dict()
        result_params = result["hits"]["hits"][0]["_source"]["parameters"]
        self.assertEqual(result_params.schemas, [])
        # test delete of schema (by readding paramset)
        proj_parameterset = ProjectParameterSet(
            schema=self.schema_proj, project=self.proj
        )
        proj_parameterset.save()
        self.schema_proj.delete()
        result = query.execute(ignore_cache=True)
        result.to_dict()
        result_params = result["hits"]["hits"][0]["_source"]["parameters"]
        self.assertEqual(result_params.schemas, [])

    def test_experiment_get_instances_from_related(self):
        """
        Test that related instances trigger an experiment re-index.
        """
        # Update username
        self.user.username = "newusername"
        self.user.save()
        search = ExperimentDocument.search()
        query = search.query("match", title="Test exp1")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].created_by.username, "newusername")

        # Update relevant ACL models and perms
        correct_acl_structure = [
            {
                "pluginId": "django_user",
                "entityId": self.user.id,
                "canDownload": False,
                "canSensitive": False,
            }
        ]
        # Update related experiment ACL perms
        self.expacl.canSensitive = False
        self.expacl.canDownload = False
        self.expacl.save()
        search = ExperimentDocument.search()
        query = search.query("match", title="Test exp1")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        # test deletion of ACLs
        self.expacl.delete()
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, [])

        # test creation of new ACL
        newacl = ExperimentACL(
            user=self.user,
            experiment=self.exp,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            canRead=True,
        )
        newacl.save()
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

    def test_dataset_get_instances_from_related(self):
        """
        Test that related instances trigger a dataset re-index.
        """
        # Update relevant ACL models and perms
        correct_acl_structure = [
            {
                "pluginId": "django_user",
                "entityId": self.user.id,
                "canDownload": False,
                "canSensitive": False,
            }
        ]
        if settings.ONLY_EXPERIMENT_ACLS:
            # Update related experiment ACL perms
            self.expacl.canSensitive = False
            self.expacl.canDownload = False
            self.expacl.save()
        else:
            # Update dataset ACL perms
            self.setacl.canSensitive = False
            self.setacl.canDownload = False
            self.setacl.save()
        search = DatasetDocument.search()
        query = search.query("match", description="test_dataset")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        # test deletion of ACLs
        if settings.ONLY_EXPERIMENT_ACLS:
            self.expacl.delete()
        else:
            self.setacl.delete()
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, [])

        # test creation of new ACL
        if settings.ONLY_EXPERIMENT_ACLS:
            newacl = ExperimentACL(
                user=self.user,
                experiment=self.exp,
                aclOwnershipType=ExperimentACL.OWNER_OWNED,
                canRead=True,
            )
        else:
            newacl = DatasetACL(
                user=self.user,
                dataset=self.dataset,
                aclOwnershipType=ProjectACL.OWNER_OWNED,
                canRead=True,
            )
        newacl.save()
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        # test that public flag updated by experiments in Macro-mode
        if settings.ONLY_EXPERIMENT_ACLS:
            # Update existing parent experiment to have public=embargoed/25
            self.exp.public_access = Experiment.PUBLIC_ACCESS_EMBARGO
            self.exp.save()
            result = query.execute(ignore_cache=True)
            self.assertEqual(result.hits[0].public_access, 25)
            # add new experiment as parent with full public access/100
            # create experiment object
            exp_public = Experiment(
                title="public exp",
                institution_name="monash",
                description="Test Description",
                created_by=self.user,
                public_access=Experiment.PUBLIC_ACCESS_FULL,
            )
            exp_public.save()
            self.dataset.experiments.add(exp_public)
            result = query.execute(ignore_cache=True)
            self.assertEqual(result.hits[0].public_access, 100)
            self.assertEqual(
                result.hits[0].experiments,
                [
                    {"id": self.exp.id, "title": self.exp.title},
                    {"id": exp_public.id, "title": exp_public.title},
                ],
            )

            # test adding an instrument
            manager_group = Group(name="Test Manager Group")
            manager_group.save()
            manager_group.user_set.add(self.user)
            facility = Facility(name="Test Facility", manager_group=manager_group)
            facility.save()
            instrument = Instrument(name="Test Instrument", facility=facility)
            instrument.save()
            self.dataset.instrument = instrument
            self.dataset.save()
            result = query.execute(ignore_cache=True)
            self.assertEqual(
                result.hits[0].instrument,
                {"id": instrument.id, "name": instrument.name},
            )

            # test changing instrument
            instrument2 = Instrument(name="Test Instrument 2", facility=facility)
            instrument2.save()
            self.dataset.instrument = instrument2
            self.dataset.save()
            result = query.execute(ignore_cache=True)
            self.assertEqual(
                result.hits[0].instrument,
                {"id": instrument2.id, "name": instrument2.name},
            )

            # Now test that deleting public exp reverts flag
            # TODO deletion doesn't work syncronously
            # exp_public.delete()
            # result = query.execute(ignore_cache=True)
            # self.assertEqual(result.hits[0].public_access, 25)
            # self.assertEqual(
            #    result.hits[0].experiments,
            #    [
            #        {"id": self.exp.id, "title": self.exp.title},
            #    ],
            # )

    def test_datafile_get_instances_from_related(self):
        """
        Test that related instances trigger a datafile re-index.
            Dataset,
        """
        # Update relevant ACL models and perms
        correct_acl_structure = [
            {
                "pluginId": "django_user",
                "entityId": self.user.id,
                "canDownload": False,
                "canSensitive": False,
            }
        ]
        if settings.ONLY_EXPERIMENT_ACLS:
            # Update related experiment ACL perms
            self.expacl.canSensitive = False
            self.expacl.canDownload = False
            self.expacl.save()
        else:
            # Update datafile ACL perms
            self.fileacl.canSensitive = False
            self.fileacl.canDownload = False
            self.fileacl.save()
        search = DataFileDocument.search()
        query = search.query("match", filename="test.txt")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        # test deletion of ACLs
        if settings.ONLY_EXPERIMENT_ACLS:
            self.expacl.delete()
        else:
            self.fileacl.delete()
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, [])

        # test creation of new ACL
        if settings.ONLY_EXPERIMENT_ACLS:
            newacl = ExperimentACL(
                user=self.user,
                experiment=self.exp,
                aclOwnershipType=ExperimentACL.OWNER_OWNED,
                canRead=True,
            )
        else:
            newacl = DatafileACL(
                user=self.user,
                datafile=self.datafile,
                aclOwnershipType=ProjectACL.OWNER_OWNED,
                canRead=True,
            )
        newacl.save()
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        # test that public flag updated by experiments in Macro-mode
        if settings.ONLY_EXPERIMENT_ACLS:
            # Update existing parent experiment to have public=embargoed/25
            self.exp.public_access = Experiment.PUBLIC_ACCESS_EMBARGO
            self.exp.save()
            result = query.execute(ignore_cache=True)
            self.assertEqual(result.hits[0].public_access, 25)
            # add new experiment as parent with full public access/100
            # create experiment object
            exp_public = Experiment(
                title="public exp",
                institution_name="monash",
                description="Test Description",
                created_by=self.user,
                public_access=Experiment.PUBLIC_ACCESS_FULL,
            )
            exp_public.save()
            self.dataset.experiments.add(exp_public)
            result = query.execute(ignore_cache=True)
            self.assertEqual(result.hits[0].public_access, 100)
            self.assertEqual(
                result.hits[0].dataset.experiments,
                [{"id": self.exp.id}, {"id": exp_public.id}],
            )

            # change dataset of datafile
            # check original
            result = query.execute(ignore_cache=True)
            self.assertEqual(
                result.hits[0].dataset,
                {
                    "id": self.dataset.id,
                    "description": self.dataset.description,
                    "experiments": [{"id": self.exp.id}],
                },
            )
            # now change to another
            dataset2 = Dataset(description="test_dataset2")
            dataset2.save()
            result = query.execute(ignore_cache=True)
            self.assertEqual(
                result.hits[0].dataset,
                {
                    "id": dataset2.id,
                    "description": dataset2.description,
                    "experiments": [],
                },
            )

            # Now test that deleting public exp reverts flag
            # TODO deletion doesn't work syncronously
            # exp_public.delete()
            # result = query.execute(ignore_cache=True)
            # self.assertEqual(result.hits[0].public_access, 25)
            # self.assertEqual(
            #    result.hits[0].dataset[0].experiments,
            #    [{"id": self.exp.id}],
            # )

    def tearDown(self):
        self.datafile.delete()
        self.dataset.delete()
        self.exp.delete()
        self.proj.delete()
        self.publicuser.delete()
        self.user.delete()
        self.user_grp.delete()
        self.user_token.delete()

        # remove post_delete signals connected in these tests
        post_delete.disconnect(update_es_relations, sender=Dataset)
        post_delete.disconnect(update_es_relations, sender=ProjectACL)
        post_delete.disconnect(update_es_relations, sender=ExperimentACL)
        post_delete.disconnect(update_es_relations, sender=DatasetACL)
        post_delete.disconnect(update_es_relations, sender=DatafileACL)
        post_delete.disconnect(update_es_relations, sender=ProjectParameterSet)
        post_delete.disconnect(update_es_relations, sender=ExperimentParameterSet)
        post_delete.disconnect(update_es_relations, sender=DatasetParameterSet)
        post_delete.disconnect(update_es_relations, sender=DatafileParameterSet)
        post_delete.disconnect(update_es_relations, sender=ProjectParameter)
        post_delete.disconnect(update_es_relations, sender=ExperimentParameter)
        post_delete.disconnect(update_es_relations, sender=DatasetParameter)
        post_delete.disconnect(update_es_relations, sender=DatafileParameter)
