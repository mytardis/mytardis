# pylint: disable=http-response-with-json-dumps,http-response-with-content-type-json
"""
views relevant for facilities and the facility view
"""

import json
import logging
import time

from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Min, Sum, When
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from ..models import DataFile, Dataset, Experiment
from ..models.facility import facilities_managed_by

logger = logging.getLogger(__name__)


def datetime_to_us(dt):
    '''
    The datetime objects are kept as None if they aren't set, otherwise
    they're converted to milliseconds so AngularJS can format them nicely.
    '''
    if dt is None:
        return None
    dt = timezone.localtime(dt)
    return time.mktime(dt.timetuple()) * 1000 + dt.microsecond / 1000


@never_cache
@login_required
def facility_overview_data_count(request, facility_id):
    '''
    returns the total number of datasets for pagination in json format
    '''

    dataset_object_count = Dataset.objects.filter(
        instrument__facility__manager_group__user=request.user,
        instrument__facility__id=facility_id
    ).count()
    return HttpResponse(
        json.dumps({'facility_data_count': dataset_object_count}),
        content_type='application/json')


@never_cache
@login_required
def facility_overview_facilities_list(request):
    '''
    json list of facilities managed by the current user
    '''
    facility_data = []
    for facility in facilities_managed_by(request.user):
        facility_data.append({"id": facility.id, "name": facility.name})

    return HttpResponse(json.dumps(facility_data),
                        content_type='application/json')


def dataset_aggregate_info(dataset):
    datafiles_all = DataFile.objects.filter(dataset=dataset)
    verified_datafiles_count = \
        DataFile.objects.filter(dataset=dataset) \
        .values('id') \
        .annotate(min_verified=Min(Case(When(file_objects__verified=True,
                                             then=1),
                                        default=0,
                                        output_field=IntegerField()))) \
        .filter(min_verified=1) \
        .order_by('id').count()
    verified_datafiles_size = \
        DataFile.objects.filter(dataset=dataset) \
        .values('id') \
        .annotate(min_verified=Min(Case(When(file_objects__verified=True,
                                             then=1),
                                        default=0,
                                        output_field=IntegerField()))) \
        .filter(min_verified=1) \
        .order_by('id') \
        .aggregate(Sum('size'))['size__sum'] or 0
    return {
        "dataset_size": DataFile.sum_sizes(datafiles_all),
        "verified_datafiles_count": verified_datafiles_count,
        "verified_datafiles_size": verified_datafiles_size,
        "datafile_count": datafiles_all.count()
    }


def facility_overview_datafile_list(dataset):
    datafile_objects = DataFile.objects.filter(dataset=dataset)
    datafiles = []
    for datafile in datafile_objects:
        if datafile.verified:
            verified = "Yes"
        else:
            verified = "No"
            try:
                file_object_size = getattr(
                    getattr(datafile.file_objects.first(),
                            'file_object', None),
                    'size', 0)
                if file_object_size < int(datafile.size):
                    verified = "No (%s of %s bytes uploaded)" \
                        % ('{:,}'.format(file_object_size),
                           '{:,}'.format(int(datafile.size)))
            except AttributeError:
                verified = "No (0 of %s bytes uploaded)" \
                    % '{:,}'.format(int(datafile.size))
            except IOError:
                verified = "No (0 of %s bytes uploaded)" \
                    % '{:,}'.format(int(datafile.size))
        datafiles.append({
            "id": datafile.id,
            "filename": datafile.filename,
            "size": int(datafile.size),
            "created_time": datetime_to_us(datafile.created_time),
            "modification_time": datetime_to_us(datafile.modification_time),
            "verified": verified,
        })
    return datafiles


@never_cache
@login_required
def facility_overview_dataset_detail(request, dataset_id):
    return HttpResponse(
        json.dumps(
            facility_overview_datafile_list(
                Dataset.objects.get(
                    instrument__facility__manager_group__user=request.user,
                    pk=dataset_id
                )
            )
        ), content_type='application/json')


@never_cache
@login_required
def facility_overview_experiments(request, facility_id, start_index,
                                  end_index):
    '''
    json facility datasets
    '''
    start_index = int(start_index)
    end_index = int(end_index)
    dataset_objects = Dataset.objects.filter(
        instrument__facility__manager_group__user=request.user,
        instrument__facility__id=facility_id
    ).order_by('-id')[start_index:end_index]

    # Select only the bits we want from the models
    facility_data = []
    for dataset in dataset_objects:
        instrument = dataset.instrument
        facility = instrument.facility
        try:
            parent_experiment = dataset.experiments.all()[:1].get()
        except Experiment.DoesNotExist:
            logger.warning("Not listing dataset id %s in Facility Overview",
                           dataset.id)
            continue

        owners = parent_experiment.get_owners()
        groups = parent_experiment.get_groups()

        dataset_info = dataset_aggregate_info(dataset)

        obj = {
            "id": dataset.id,
            "parent_experiment": {
                "id": parent_experiment.id,
                "title": parent_experiment.title,
            },
            "created_time": datetime_to_us(dataset.created_time),
            "description": dataset.description,
            "institution": parent_experiment.institution_name,
            "datafile_count": dataset_info['datafile_count'],
            "size": dataset_info['dataset_size'],
            "verified_datafiles_count": dataset_info['verified_datafiles_count'],
            "verified_datafiles_size": dataset_info['verified_datafiles_size'],
            "owner": ', '.join([o.username for o in owners]),
            "group": ', '.join([g.name for g in groups]),
            "instrument": {
                "id": instrument.id,
                "name": instrument.name,
            },
            "facility": {
                "id": facility.id,
                "name": facility.name,
            },
        }
        facility_data.append(obj)

    return HttpResponse(json.dumps(facility_data), content_type='application/json')
