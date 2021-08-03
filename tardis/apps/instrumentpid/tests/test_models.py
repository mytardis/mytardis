from django.test import TestCase
from django.contrib.auth.models import Group
from django.db import IntegrityError
from tardis.tardis_portal.models.facility import Facility
from tardis.tardis_portal.models.instrument import Instrument


class ModelsTestCase(TestCase):
    def test_model_has_pid(self):
        group = "testgroup"
        group = Group.objects.create(
            name=group,
        )
        group.save()
        facility = Facility.objects.create(name="Test Facility", manager_group=group)
        facility.save()
        instrument = Instrument.objects.create(name="Instrument", facility=facility)
        instrument.save()
        self.assertTrue(hasattr(instrument, "pid"))

    def test_adding_value_to_pid(self):
        group = "testgroup"
        group = Group.objects.create(
            name=group,
        )
        group.save()
        facility = Facility.objects.create(name="Test Facility", manager_group=group)
        facility.save()
        instrument = Instrument.objects.create(name="Instrument", facility=facility)
        instrument.save()
        pid = "my_test_pid"
        instrument.pid.pid = pid
        instrument.pid.save()
        key = instrument.id
        instrument = Instrument.objects.get(pk=key)
        self.assertTrue(instrument.pid.pid == pid)

    def test_duplicate_pids_raises_error(self):
        group = "testgroup"
        group = Group.objects.create(
            name=group,
        )
        group.save()
        facility = Facility.objects.create(name="Test Facility", manager_group=group)
        facility.save()
        instrument1 = Instrument.objects.create(name="Instrument1", facility=facility)
        instrument1.save()
        instrument2 = Instrument.objects.create(name="Instrument2", facility=facility)
        instrument2.save()
        pid = "my_test_pid"
        instrument1.pid.pid = pid
        instrument1.pid.save()
        with self.assertRaises(IntegrityError):
            instrument2.pid.pid = pid
            instrument2.pid.save()
