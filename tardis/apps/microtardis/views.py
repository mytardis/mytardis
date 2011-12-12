import os
import Image
import imghdr

from django.template import Context
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.conf import settings

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.shortcuts import render_response_index
from tardis.tardis_portal.staging import add_datafile_to_dataset
from tardis.tardis_portal.staging import write_uploaded_file_to_dataset

from tardis.tardis_portal.models import DatafileParameterSet
from tardis.tardis_portal.models import Schema
from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.models import Dataset_File

@never_cache
@authz.datafile_access_required
def retrieve_parameters(request, dataset_file_id):
    # get schema id of EDAX Genesis spectrum schema
    schema_spc = Schema.objects.filter(name="EDAXGenesis_SPC")
    schema_ids_spc = []
    for schema in schema_spc:
        schema_ids_spc.append(schema.id)
    field_order_spc = ["Sample Type (Label)", "Preset", "Live Time", "Acc. Voltage"]
    
    # get schema id of EXIF image metadata schema
    schema_exif = Schema.objects.filter(name__endswith="EXIF")
    schema_ids_exif = []
    for schema in schema_exif:
        schema_ids_exif.append(schema.id)
    field_order_exif = ["[User] Date", "[User] Time"]

    datafileparametersets = DatafileParameterSet.objects.filter(dataset_file__pk=dataset_file_id)
    parametersets = {}
    for parameterset in datafileparametersets:
        unsorted = {}
        sorted = []
        # get list of parameters
        parameters = parameterset.datafileparameter_set.all()
        for parameter in parameters:
            unsorted[str(parameter.name.full_name)] = parameter
                
        # sort spectrum tags
        if parameterset.schema.id in schema_ids_spc:
            # sort spectrum tags defined in field_order_spc                
            for field in field_order_spc:
                if field in unsorted:
                    sorted.append(unsorted[field])
                    unsorted.pop(field)
            # sort atomic peak numbers
            peaks = []
            for field in unsorted:
                if field.startswith("Peak ID Element"):
                    peaks.append(field)
            peaks.sort(key=lambda peak: int(peak.split(" ")[-1])) 
            for field in peaks:
                sorted.append(unsorted[field])
                unsorted.pop(field)
            # sort the rest of unsorted parameters
            if unsorted:
                sorted_keys = unsorted.keys()
                sorted_keys.sort()
                for key in sorted_keys:
                    sorted.append(unsorted[key])
            parametersets[parameterset.schema] = sorted
        # sort exif tags
        elif parameterset.schema.id in schema_ids_exif:
            # sort exif metadata tags defined in field_order_exif
            for field in field_order_exif:
                if field in unsorted:
                    sorted.append(unsorted[field])
                    unsorted.pop(field)
            # sort the rest of unsorted parameters
            if unsorted:
                sorted_keys = unsorted.keys()
                sorted_keys.sort()
                for key in sorted_keys:
                    sorted.append(unsorted[key])
            parametersets[parameterset.schema] = sorted
        # use default order
        else:
            parametersets[parameterset.schema] = parameters
    
    thumbpath = None
    qs = Dataset_File.objects.filter(id=dataset_file_id)
    if qs:
        datafile = qs[0]
        basepath = "/thumbnails"
        img_path = str(datafile.url)
        if img_path.endswith(".tif"):
            extention = "_tif_thumb.jpg"
        elif img_path.endswith(".spc"):
            extention = "_spc_thumb.jpg"
        thumbpath = get_thumbnail_path(basepath, datafile, img_path, extention)

    c = Context({'parametersets': parametersets,
                 'thumbpath': thumbpath,})

    return HttpResponse(render_response_index(request,
                        'parameters_mt.html', c))

def get_thumbnail_path(basepath, datafile, img_path, extention):
    experiment_id = str(datafile.dataset.experiment.id)
    dataset_id = str(datafile.dataset.id)
    parts = img_path.split('/')
    instrument = parts[-2]
    filename = parts[-1]
    doc_idx = filename.rindex('.')
    thumbname = filename[:doc_idx] + extention
    thumbpath = os.path.join(basepath, experiment_id, dataset_id, instrument, thumbname)
    
    return thumbpath
    

def write_thumbnails(datafile, img, img_path, extention):
    img.thumbnail( (400, 400), Image.ANTIALIAS )
    basepath = settings.THUMBNAILS_PATH
    thumbpath = get_thumbnail_path(basepath, datafile, img_path, extention)
    dirpath = thumbpath[:thumbpath.rindex('/')]
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    out = file(thumbpath, "w")
    try:
        img.save(out, "JPEG")
    finally:
        out.close()
        
def display_thumbnails(request, experiment_id, dataset_id, instrument, filename):
    basepath = settings.THUMBNAILS_PATH
    thumbpath = os.path.join(basepath, experiment_id, dataset_id, instrument, filename)
    image_data = open(thumbpath, "rb").read()

    return HttpResponse(image_data, mimetype="image/jpeg")