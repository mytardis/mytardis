from graphql_relay import to_global_id
from graphql_jwt.testcases import JSONWebTokenTestCase
from django.contrib.auth.models import User, Group, Permission

from ...models.facility import Facility


class facilitiesTestCase(JSONWebTokenTestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="bob",
            password="bobby*312",
            email="bob@bobby.com.au",
            is_active=True
        )
        self.group = Group(
            name="Test Group"
        )
        self.group.save()
        self.group.user_set.add(self.user)
        self.client.authenticate(self.user)

    def tearDown(self):
        self.client.logout()
        Facility.objects.all().delete()
        self.group.delete()
        self.user.delete()


class getFacilitiesTestCase(facilitiesTestCase):

    def setUp(self):
        super().setUp()
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_facility")
        )
        self.facility = Facility(
            name="Test Facility",
            manager_group=self.group
        )
        self.facility.save()

    def test_get_facilities(self):
        query = '''
        {
            facilities {
                edges {
                    node {
                        pk
                        name
                        managerGroup {
                            pk
                            name
                        }
                    }
                }
            }
        }
        '''
        rsp = self.client.execute(query).to_dict()
        self.assertFalse('errors' in rsp)
        self.assertTrue('data' in rsp)
        data = rsp['data']
        self.assertTrue('facilities' in data)
        facilities = data['facilities']
        self.assertTrue('edges' in facilities)
        edges = facilities['edges']
        self.assertEqual(len(edges), 1)
        facility = edges[0]['node']
        self.assertEqual(facility['pk'], self.facility.id)
        self.assertEqual(facility['name'], self.facility.name)
        self.assertTrue('managerGroup' in facility)
        group = facility['managerGroup']
        self.assertEqual(group['pk'], self.group.id)
        self.assertEqual(group['name'], self.group.name)


class createFacilityTestCase(facilitiesTestCase):

    def setUp(self):
        super().setUp()
        self.user.user_permissions.add(
            Permission.objects.get(codename="add_facility")
        )

    def test_create_facility(self):
        facilityName = "Hello!"
        query = '''
        mutation createFacility($input: CreateFacilityInput!) {
            createFacility(input: $input) {
                facility {
                    name
                    managerGroup {
                        name
                    }
                }
            }
        }
        '''
        variables = {
            'input': {
                'name': facilityName,
                'managerGroup': to_global_id("GroupType", self.group.id)
            }
        }
        rsp = self.client.execute(query, variables).to_dict()
        self.assertFalse('errors' in rsp)
        self.assertTrue('data' in rsp)
        self.assertTrue('createFacility' in rsp['data'])
        data = rsp['data']['createFacility']
        self.assertTrue('facility' in data)
        facility = data['facility']
        self.assertEqual(facility['name'], facilityName)
        self.assertTrue('managerGroup' in facility)
        group = facility['managerGroup']
        self.assertEqual(group['name'], self.group.name)


class updateFacilityTestCase(facilitiesTestCase):

    def setUp(self):
        super().setUp()
        self.user.user_permissions.add(
            Permission.objects.get(codename="change_facility")
        )
        self.facility = Facility(
            name="Test Facility",
            manager_group=self.group
        )
        self.facility.save()

    def test_update_facility(self):
        facilityName = "Hello!"
        query = '''
        mutation updateFacility($input: UpdateFacilityInput!) {
            updateFacility(input: $input) {
                facility {
                    pk
                    name
                }
            }
        }
        '''
        variables = {
            'input': {
                'id': to_global_id("FacilityType", self.facility.id),
                'name': facilityName
            }
        }
        rsp = self.client.execute(query, variables).to_dict()
        self.assertFalse('errors' in rsp)
        self.assertTrue('data' in rsp)
        self.assertTrue('updateFacility' in rsp['data'])
        data = rsp['data']['updateFacility']
        self.assertTrue('facility' in data)
        facility = data['facility']
        self.assertEqual(facility['name'], facilityName)
        facility = Facility.objects.get(id=facility['pk'])
        self.assertTrue(facility.name, facilityName)
