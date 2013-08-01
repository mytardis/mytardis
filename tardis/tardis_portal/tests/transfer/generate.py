#
# Copyright (c) 2012-2013, Centre for Microscopy and Microanalysis
#   (University of Queensland, Australia)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the  University of Queensland nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# Utility functions for generating test objects.
import os, urlparse

from django.conf import settings
from tardis.test_settings import FILE_STORE_PATH
from tardis.tardis_portal.models import Location

def generate_datafile(path, dataset, content=None, size=-1, 
                      verify=True, verified=True, time=None):
    '''Generates a datafile AND a replica to hold its contents'''
    from tardis.tardis_portal.models import Dataset_File, Replica, Location

    saved = settings.REQUIRE_DATAFILE_CHECKSUMS
    settings.REQUIRE_DATAFILE_CHECKSUMS = False
    try:
        datafile = Dataset_File()
        if content:
            datafile.size = str(len(content))
        else:
            datafile.size = str(size)
        # Normally we use any old string for the datafile path, but some
        # tests require the path to be the same as what 'staging' would use
        if path == None:
            datafile.dataset_id = dataset.id
            datafile.save()
            path = "%s/%s/%s" % (dataset.get_first_experiment().id,
                                 dataset.id, datafile.id)

        filepath = os.path.normpath(FILE_STORE_PATH + '/' + path)
        if content:
            try:
                os.makedirs(os.path.dirname(filepath))
                os.remove(filepath)
            except:
                pass
            file = open(filepath, 'wb+')
            file.write(content)
            file.close()
        datafile.mimetype = "application/unspecified"
        datafile.filename = os.path.basename(filepath)
        datafile.dataset_id = dataset.id
        datafile.created_time = time
        datafile.modification_time = time
        datafile.save()

        location = _infer_location(path)
        replica = Replica(datafile=datafile, url=path, protocol='',
                          location=location)
        if verify and content:
            if not replica.verify(allowEmptyChecksums=True):
                raise RuntimeError('verify failed!?!')
        else:
            replica.verified = verified
        replica.save()
        return (datafile, replica)
    finally:
        settings.REQUIRE_DATAFILE_CHECKSUMS = saved

def _infer_location(path):
    if urlparse.urlparse(path).scheme == '':
        loc = Location.get_default_location()
    else:
        loc = Location.get_location_for_url(path)
    if loc:
        return loc
    else:
        raise Exception('Cannot infer a location for %s' % path)

def generate_dataset(datafiles=[], experiments=[]):
    from tardis.tardis_portal.models import Dataset
    dataset = Dataset()
    dataset.save()
    for df in datafiles:
        df.dataset_id = dataset.id
        df.save()
    for exp in experiments:
        dataset.experiments.add(exp)
    dataset.save()
    return dataset

def generate_experiment(datasets=[], users=[], title='', url=''):
    from tardis.tardis_portal.models import Experiment, ObjectACL
    experiment = Experiment(created_by=users[0],
                            title=title,
                            url=url)
    experiment.save()
    for ds in datasets:
        ds.experiments.add(experiment)
        ds.save()
    for user in users:
        acl = ObjectACL(content_object=experiment,
                        pluginId='django_user',
                        entityId=str(user.id),
                        isOwner=True,
                        canRead=True,
                        canWrite=True,
                        canDelete=True,
                        aclOwnershipType=ObjectACL.OWNER_OWNED)
        acl.save()
    return experiment

def generate_user(name, priority=-1):
    from django.contrib.auth.models import User
    from tardis.apps.migration.models import UserPriority, DEFAULT_USER_PRIORITY
    from tardis.tardis_portal.models import UserProfile
    user = User(username=name)
    user.save()
    UserProfile(user=user).save()
    if priority >= 0 and priority != DEFAULT_USER_PRIORITY:
        UserPriority(user=user,priority=priority).save()
    return user
