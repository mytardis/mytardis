from django.db import models
from tardis.tardis_portal.models import Facility


class Snapshot(models.Model):
    facility = models.ForeignKey(Facility,
                                 on_delete=models.DO_NOTHING,
                                 null=True,
                                 )
    storage = models.BigIntegerField(null=True)
    files = models.BigIntegerField(null=True)
    datasets = models.BigIntegerField(null=True)
    experiments = models.BigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def get_latest_snapshot(facility_id=None):
        snapshot = {}
        if facility_id:
            snapshot = Snapshot.objects.filter(facility_id=facility_id).order_by('-created_at').first()
        else:
            snapshot = Snapshot.objects.filter(facility_id=None).order_by('-created_at').first()

        return snapshot
