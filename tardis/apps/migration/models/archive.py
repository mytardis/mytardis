#
# Copyright (c) 2013, Centre for Microscopy and Microanalysis
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
#    * Neither the name of the University of Queensland nor the
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


from django.db import models

class Archive(models.Model):
    """
    This class is the descriptor for an archive of a MyTardis Experiment.
    
    The 'experiment' linkage is designed to be fragile so that we can 
    delete the actual 'Experiment' from the MyTardis database and still
    keep the archive record.
    
    :attribute experiment_owner: the name of the experiment's owning user 
    at the time the archive was created.
    :attribute experiment_title: the title of the experiment at the time 
    the archive was created.
    :attribute experiment_url: the URL of the experiment.  This should 
    be stable.
    :attribute archive_url: the URL where the archive was stored.
    :attribute archive_created: the timestamp for the archive creation
    :attribute nos_files: the number of files in the archive
    :attribute nos_errors: the number of errors (missing / unreadable files) 
    encountered while creating the archive 
    :attribute size: the archive size in bytes
    :attribute sha512sum: the archive checksum (optional)
    :attribute mimetype: the archive mimetype (e.g. 'application/x-tar')
    :attribute encoding: the archive encoding (e.g. 'x-gzip')

    The 'experiment_changed' timestamp is the timestamp for the last change
    to the experiment as saved in the archive.  This is to allow incremental
    archive creation.

    Note that it is not mandatory to persist the archive record for an
    archive.
    """

    from tardis.tardis_portal.models import Experiment
    
    experiment = models.ForeignKey(Experiment, unique=False, 
                                   on_delete=models.SET_NULL, null=True)
    experiment_owner =  models.CharField(max_length=30)
    experiment_title = models.CharField(max_length=400)
    archive_created = models.DateTimeField(auto_now_add=True)
    experiment_changed = models.DateTimeField(null=True)
    experiment_url = models.URLField(verify_exists=False, max_length=255,
                                     null=False, blank=False)
    archive_url = models.URLField(verify_exists=False, max_length=255,
                                  null=False, blank=False)
    nos_files = models.IntegerField(null=False)
    nos_errors = models.IntegerField(null=False)
    size = models.BigIntegerField(null=False)
    sha512sum = models.CharField(blank=True, max_length=128)
    mimetype = models.CharField(blank=False, max_length=80)
    encoding = models.CharField(max_length=80)

    class Meta:
        app_label = 'migration'

