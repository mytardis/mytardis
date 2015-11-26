"""
views relevant for facilities and the facility view
"""

import json
import logging
import time

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from tardis.tardis_portal.models import Dataset, Experiment, DataFile
from tardis.tardis_portal.models.facility import facilities_managed_by

logger = logging.getLogger(__name__)


@never_cache
@login_required
def fetch_facility_data_count(request, facility_id):
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
def fetch_facility_data(request, facility_id, start_index, end_index):
    '''
    json facility datasets
    '''

    dataset_objects = Dataset.objects.filter(
        instrument__facility__manager_group__user=request.user,
        instrument__facility__id=facility_id
    ).order_by('-id')[start_index:end_index]

    def datetime_to_us(dt):
        '''
        The datetime objects are kept as None if they aren't set, otherwise
        they're converted to milliseconds so AngularJS can format them nicely.
        '''
        if dt is None:
            return None
        dt = timezone.localtime(dt)
        return time.mktime(dt.timetuple()) * 1000 + dt.microsecond / 1000

    # Select only the bits we want from the models
    facility_data = []
    for dataset in dataset_objects:
        instrument = dataset.instrument
        facility = instrument.facility
        try:
            parent_experiment = dataset.experiments.all()[:1].get()
        except Experiment.DoesNotExist:
            logger.warning("Not listing dataset id %d in Facility Overview" % dataset.id)
            continue
        datafile_objects = DataFile.objects.filter(dataset=dataset)
        owners = parent_experiment.get_owners()
        groups = parent_experiment.get_groups()
        datafiles = []
        dataset_size = 0
        verified_datafiles_count = 0
        verified_datafiles_size = 0
        for datafile in datafile_objects:
            if datafile.verified:
                verified = "Yes"
                verified_datafiles_count += 1
                verified_datafiles_size += datafile.size
            else:
                verified = "No"
                try:
                    file_object_size = getattr(
                        getattr(datafile.file_objects.first(),
                                'file_object', None),
                        'size', 0)
                    if file_object_size < datafile.size:
                        verified = "No (%s of %s bytes uploaded)" \
                            % ('{:,}'.format(file_object_size),
                               '{:,}'.format(datafile.size))
                except AttributeError:
                    verified = "No (0 of %s bytes uploaded)" \
                        % '{:,}'.format(datafile.size)
                except IOError, e:
                    verified = "No (0 of %s bytes uploaded)" \
                        % '{:,}'.format(datafile.size)
            datafiles.append({
                "id": datafile.id,
                "filename": datafile.filename,
                "size": datafile.size,
                "created_time": datetime_to_us(datafile.created_time),
                "modification_time": datetime_to_us(datafile.modification_time),
                "verified": verified,
            })
            dataset_size = dataset_size + datafile.size
        obj = {
            "id": dataset.id,
            "parent_experiment": {
                "id": parent_experiment.id,
                "title": parent_experiment.title,
                "created_time": datetime_to_us(parent_experiment.created_time),
            },
            "description": dataset.description,
            "institution": parent_experiment.institution_name,
            "datafiles": datafiles,
            "size": dataset_size,
            "verified_datafiles_count": verified_datafiles_count,
            "verified_datafiles_size": verified_datafiles_size,
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


@never_cache
@login_required
def fetch_facilities_list(request):
    '''
    json list of facilities managed by the current user
    '''
    facility_data = []
    for facility in facilities_managed_by(request.user):
        facility_data.append({"id": facility.id, "name": facility.name})

    return HttpResponse(json.dumps(facility_data), content_type='application/json')
