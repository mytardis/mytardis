import unittest
from io import StringIO

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.test import TestCase, override_settings
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
)
from tardis.tardis_portal.models import (
    DataFile,
    Dataset,
    Experiment,
    Token,
    DatafileACL,
    DatasetACL,
    ExperimentACL,
)


"""
TODO improve these tests to include the following:
 - fix ACL tests
 - add parameter tests for all objects
   - test types of parameters index properly
 - test Indexing works for all object relations
"""


@unittest.skipUnless(is_es_online(), "Elasticsearch is offline")
@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class IndexTestCase(TestCase):
    def setUp(self):
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
        self.user_grp = User.objects.create_user(user_token, email_token, pwd)
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

        # create experiment object
        self.exp = Experiment(
            title="test exp1",
            institution_name="monash",
            description="Test Description",
            created_by=self.user,
        )
        self.exp.save()

        # create dataset object
        # dataset1 belongs to experiment1
        self.dataset = Dataset(description="test_dataset")
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()

        # create datafile object
        settings.REQUIRE_DATAFILE_SIZES = False
        settings.REQUIRE_DATAFILE_CHECKSUMS = False
        self.datafile = DataFile(dataset=self.dataset, filename="test.txt")
        self.datafile.save()

    def test_create_index(self):
        """
        Test the existance of document objects
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
        # Explicit ACL creation for group+token for project
        print("creating project group + token ACLs")
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
        print("creating experiment group + token ACLs")
        # Explicit ACL creation for group+token for experiment
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
        print("creating dataset group + token ACLs")
        # Explicit ACL creation for group+token for dataset
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
        print("creating datafile group + token ACLs")
        # Explicit ACL creation for group+token for datafile
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
            {"pluginId": "django_group", "entityId": self.group.id},
            {"pluginId": "django_user", "entityId": self.user.id},
        ]

        self.proj.description = "updated description"
        self.proj.save()

        search = ProjectDocument.search()
        query = search.query("match", name="Test Project 1")
        result = query.execute(ignore_cache=True)
        print(result.hits[0].description)
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        search = ExperimentDocument.search()
        query = search.query("match", title="test exp1")
        result = query.execute(ignore_cache=True)
        print(result.hits[0])
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        search = DatasetDocument.search()
        query = search.query("match", description="test_dataset")
        result = query.execute(ignore_cache=True)
        print(result.hits[0])
        self.assertEqual(result.hits[0].acls, correct_acl_structure)

        search = DataFileDocument.search()
        query = search.query("match", filename="test.txt")
        result = query.execute(ignore_cache=True)
        print(result.hits[0])

        self.assertEqual(result.hits[0].acls, correct_acl_structure)
