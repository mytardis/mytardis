from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Count, Sum

from tardis.apps.usage_stats.models import Snapshot
from tardis.tardis_portal.models import (DataFile, Dataset, Experiment,
                                         Facility, ObjectACL)


class Command(BaseCommand):
    help = "Takes snapshot of disk usage"

    def handle(self, *args, **options):
        # get latest stats
        cursor = connection.cursor()
        if cursor.db.vendor == 'postgresql':
            cursor.execute("SELECT SUM(size::bigint) FROM tardis_portal_datafile")
            try:
                datafile_size = int(cursor.fetchone()[0])
            except TypeError:
                datafile_size = 0
        else:
            datafile_size = DataFile.sum_sizes(DataFile.objects.all())

        c = {
            'experiment_count': Experiment.objects.all().count(),
            'dataset_count': Dataset.objects.all().count(),
            'datafile_count': DataFile.objects.all().count(),
            'datafile_size': datafile_size
        }

        self._create_snapshot(c['datafile_size'], c['datafile_count'],
                              c['dataset_count'], c['experiment_count'])
        

        # now do it for facilities
        facilities = Facility.objects.annotate(
            datafile_size_sum=Sum('instrument__dataset__datafile__size'),
            datafile_count=Count('instrument__dataset__datafile'),
            dataset_count=Count('instrument__dataset'),
        ).all()

        for facility in facilities:
            self._create_snapshot(facility.datafile_size_sum, facility.datafile_count,
                                  facility.dataset_count, None, facility)
    
    def _create_snapshot(self, storage=None, files=None, datasets=None,
                         experiments=None, facility=None):
        self.stdout.write(  
            self.style.SUCCESS('Creating snapshot')
        )

        self.stdout.write(
             self.style.SUCCESS(f'Storage: {storage}, Files: {files}, Datasets: {datasets}, Experiments: {experiments}, Facility: {facility}')
        )

        Snapshot.objects.create(
            facility=facility,
            storage=storage,
            files=files,
            datasets=datasets,
            experiments=experiments
        )
            
        self.stdout.write(
            self.style.SUCCESS('SUCCESS')
        )
