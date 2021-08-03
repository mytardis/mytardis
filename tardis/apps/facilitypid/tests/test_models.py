from django.test import TestCase
from django.contrib.auth.models import Group
from django.db import IntegrityError
from tardis.tardis_portal.models.facility import Facility


class ModelsTestCase(TestCase):
    def test_model_has_pid(self):
        group = "testgroup"
        group = Group.objects.create(
            name=group,
        )
        group.save()
        facility = Facility.objects.create(name="Test Facility", manager_group=group)
        facility.save()
        self.assertTrue(hasattr(facility, "pid"))

    def test_adding_value_to_pid(self):
        group = "testgroup"
        group = Group.objects.create(
            name=group,
        )
        group.save()
        facility = Facility.objects.create(name="Test Facility", manager_group=group)
        facility.save()
        pid = "my_test_pid"
        facility.pid.pid = pid
        facility.pid.save()
        key = facility.id
        facility = Facility.objects.get(pk=key)
        self.assertTrue(facility.pid.pid == pid)

    def test_duplicate_pids_raises_error(self):
        group = "testgroup"
        group = Group.objects.create(
            name=group,
        )
        group.save()
        facility1 = Facility.objects.create(name="Test Facility", manager_group=group)
        facility1.save()
        facility2 = Facility.objects.create(name="Test Facility", manager_group=group)
        facility2.save()
        pid = "my_test_pid"
        facility1.pid.pid = pid
        facility1.pid.save()
        with self.assertRaises(IntegrityError):
            facility2.pid.pid = pid
            facility2.pid.save()
