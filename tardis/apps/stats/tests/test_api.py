import json
from random import randint

from django.conf import settings

from tardis.tardis_portal.models import Experiment, Dataset, DataFile, ObjectACL
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.tests.api import MyTardisResourceTestCase

from tardis.apps.stats.tasks import update_user_stats


class UserStatsTest(MyTardisResourceTestCase):

    def setUp(self):
        super().setUp()
        settings.REQUIRE_DATAFILE_CHECKSUMS = False
        self.num_experiments = 1  # super().setUp() will create testexp
        self.num_datasets = 0
        self.num_datafiles = 0
        self.total_size = 0
        self.exp_ids = []
        for e in range(3, 10):
            exp = Experiment(
                title="Test Experiment {}".format(e),
                institution_name="Monash",
                description="Test Description",
                created_by=self.user)
            exp.save()
            self.num_experiments += 1
            acl = ObjectACL(
                content_type=exp.get_ct(),
                object_id=exp.id,
                pluginId=django_user,
                entityId=str(self.user.id),
                canRead=True,
                canWrite=True,
                canDelete=True,
                isOwner=True,
                aclOwnershipType=ObjectACL.OWNER_OWNED)
            acl.save()
            for s in range(3, 10):
                dataset = Dataset(
                    description="Test Dataset {}-{}".format(e, s))
                dataset.save()
                dataset.experiments.add(exp)
                dataset.save()
                self.num_datasets += 1
                for f in range(3, 10):
                    filesize = randint(1000, 10000)
                    datafile = DataFile(
                        dataset=dataset,
                        filename="{}-{}-{}.jpg".format(e, s, f),
                        size=filesize)
                    datafile.save()
                    self.num_datafiles += 1
                    self.total_size += filesize
            self.exp_ids.append(exp.id)

    def tearDown(self):
        for eid in self.exp_ids:
            exp = Experiment.objects.get(id=eid)
            exp.delete()
        super().tearDown()

    def test_update_task_and_results(self):
        update_user_stats()
        response = self.api_client.get(
            "/api/v1/stats/",
            authentication=self.get_credentials())
        data = json.loads(response.content.decode())
        self.assertEqual(data["last"]["login"], None)
        totals = data["total"]
        self.assertEqual(totals["experiments"]["value"], self.num_experiments)
        self.assertEqual(totals["datasets"]["value"], self.num_datasets)
        self.assertEqual(totals["datafiles"]["value"], self.num_datafiles)
        self.assertEqual(totals["size"]["value"], self.total_size)
