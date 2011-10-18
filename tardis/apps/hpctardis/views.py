# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2011, RMIT e-Research Office
#   (RMIT University, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from django.http import HttpResponse,HttpResponseRedirect
from tardis.tardis_portal.shortcuts import render_response_index
from django.conf import settings
from django.shortcuts import render_to_response

from tardis.tardis_portal.models import Experiment, ExperimentParameter, \
    DatafileParameter, DatasetParameter, ExperimentACL, Dataset_File, \
    DatafileParameterSet, ParameterName, GroupAdmin, Schema, \
    Dataset, ExperimentParameterSet, DatasetParameterSet, \
    UserProfile, UserAuthentication

from tardis.tardis_portal.auth.localdb_auth import django_user, django_group
from tardis.tardis_portal.auth.localdb_auth import auth_key as localdb_auth_key
from tardis.tardis_portal.auth import login, auth_service

from os import walk, path
from tardis.tardis_portal import models, forms
from tardis.tardis_portal.staging import add_datafile_to_dataset,\
    get_staging_path,stage_file,get_full_staging_path

def test(request):
    return HttpResponse(render_response_index(request,'hpctardis/test.html'))

def protocol(request,dl):
    html="Test for protocol"
 
#   dl = request.FILES['file']
        
    f = open('Test.txt','wb+')
    for chunk in dl.chunks():
        f.write(chunk)
    f.close()
    
    metadata = {}
    
    f = open('Test.txt')
    for line in f: 
        key,value = line.split(':')
        metadata[key] = value
    f.close()
    
    user    = metadata['Username']
    author  = metadata['Name']
    title   = metadata['Experiment']
    ds_desc = metadata['Facility']
    desc    = metadata['Description']
    
    html = html + desc 
    return HttpResponse(html)

def login(request):

    from tardis.tardis_portal.staging import get_full_staging_path    
    # Basic Authentication  
    if 'username' in request.POST and \
            'password' in request.POST:
        authMethod = request.POST['authMethod']
        
        user = auth_service.authenticate(
            authMethod=authMethod, request=request)

        if user:
            dl = request.FILES['file']
            staging = settings.STAGING_PATH + '/' +str(user)+ '/' 
            
            #if staging:
            #   c['directory_listing'] = staging_traverse(staging)
            #   c['staging_mount_prefix'] = settings.STAGING_MOUNT_PREFIX

            eid,exp,ds_desc = createhpcexperiment(request,user,dl)
#           addfiles(request,eid,exp,ds_desc)
            next = str(staging) + str(eid)  + '@' + str(eid)
            return HttpResponse(next)
        else:
            next = 'Unsuccessful' 
            return HttpResponse(next)
    else:
        return HttpResponse("No username password entered")    
    
def createhpcexperiment(request,user,dl):
 
    from django.contrib.auth.models import User
    from tardis.tardis_portal.views import _registerExperimentDocument
    import os 
    import tempfile

    
    #TODO 
    temp = tempfile.TemporaryFile()
    for chunk in dl.chunks():
        temp.write(chunk)
    temp.seek(0)
        
    metadata = {}

    for line in temp:
        key,value = line.split(':')
        metadata[key] = value
    temp.close()
      
#   f = open('Test.txt')
#   for line in f: 
#       key,value = line.split(':')
#       metadata[key] = value
#   f.close()
    
    # user    = metadata['Username']
    author  = metadata['Name']
    title   = metadata['Experiment']
    ds_desc = metadata['Facility']
    desc    = metadata['Description']
    
    exp = Experiment(title=title,
                     institution_name="RMIT University",
                     description=desc,
                     created_by=User.objects.get(id=user.pk),
                     )
    exp.save()
    eid = exp.id
    # Store the author for the dataset
    ae = models.Author_Experiment(experiment=exp,
                                        author=author,
                                        order='1')
    ae.save()
    
    auth_key = settings.DEFAULT_AUTH
    
    try:
        e = Experiment.objects.get(pk=eid)
    except Experiment.DoesNotExist:
        logger.exception('Experiment for eid %i in CreateHPCExperiment does not exist' % eid)
        
    acl = ExperimentACL(experiment=e,
                        pluginId=django_user,
                        entityId=str(user.id),
                        canRead=True,
                        canWrite=True,
                        canDelete=True,
                        isOwner=True,
                        aclOwnershipType=ExperimentACL.OWNER_OWNED)
    acl.save()
    
    return eid,exp,ds_desc


def addfiles(request):
    
    import os
    from os.path import basename
    from os import path
    from tardis.tardis_portal.models import Dataset_File
    
    if 'username' in request.POST and \
            'password' in request.POST:
        authMethod = request.POST['authMethod']
        
        user = auth_service.authenticate(
            authMethod=authMethod, request=request)

    if user:
        eid  = request.POST['eid']
        desc = request.POST['desc']
    #   TODO ask Ian about the error  
    #   staging = get_full_staging_path(user)
        staging = path.join(settings.STAGING_PATH,str(user),str(eid))
        filelist = []
        ds_desc  = {}
        for root, dirs, files in os.walk(staging):
            for named in dirs:
                currentdir = str(named)
        for root, dirs, files in os.walk(staging):       
            for namef in files:                       
                currentfile = path.join(currentdir,namef)
                filelist.append(currentfile)
        
        next = str(filelist)   
        ds_desc[desc] = filelist
    
#   TODO Use the try and except
   
        auth_key = settings.DEFAULT_AUTH
        try:
            exp = Experiment.objects.get(pk=eid)
        except Experiment.DoesNotExist:
            logger.exception('Experiment for eid %i in addfiles does not exist' % eid)
        
#      exp = Experiment.objects.get(pk=eid)


        for d, df in ds_desc.items():
            dataset = models.Dataset(description=d,
                                     experiment=exp)
            dataset.save()
        
            for f in df:
                filepath = path.join(staging,f)
                size = path.getsize(filepath)
                filename = path.basename(filepath)
    
                datafile = Dataset_File(dataset=dataset, filename=filename,
                                           url=filepath, size=size, protocol='staging')
                datafile.save()
                
        next = next + ' File path :' + staging
                
        return  HttpResponse(next)
    else:
        return  HttpResponse("UnSuccessful")