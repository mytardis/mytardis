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


from urllib2 import Request, urlopen, HTTPError, URLError
from urllib import quote
from urlparse import urlparse, urljoin
from tempfile import NamedTemporaryFile
from tarfile import TarFile, TarInfo
import os, tarfile, shutil, os.path

from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User

from tardis.tardis_portal.metsexporter import MetsExporter

from tardis.apps.migration import ArchivingError
from tardis.apps.migration.models import Archive
from tardis.tardis_portal.models import \
    Experiment, Dataset, Dataset_File, Replica, Location

import logging

logger = logging.getLogger(__name__)

def create_experiment_archive(exp, outfile, minSize=None, maxSize=None):
    """Create an experiment archive for 'exp' writing it to the 
    file object given by 'outfile'.  The archive is in tar/gzip
    format, and contains a METs manifest and the data files for
    all Datasets currently in the Experiment.

    On completion, 'outfile' is closed.  The result is a mostly populated
    Archive record that has not been persisted.
    """

    nos_errors = 0
    nos_files = 0
    with NamedTemporaryFile() as manifest:
        tf = tarfile.open(mode='w:gz', fileobj=outfile)
        MetsExporter().export_to_file(exp, manifest)
        manifest.flush()
        # (Note to self: path creation by string bashing is correct
        # here because these are not 'os' paths.  They are paths in 
        # the namespace of a TAR file, and '/' is always the separator.)
        tf.add(manifest.name, arcname=('%s/Manifest' % exp.id))
        for datafile in exp.get_datafiles():
            replica = datafile.get_preferred_replica(verified=True)
            f = None
            try:
                fetched = False
                fdst = NamedTemporaryFile(prefix='mytardis_tmp_ar_')
                try:
                    f = datafile.get_file()
                    shutil.copyfileobj(f, fdst)
                except Exception:
                    logger.warn("Unable to fetch %s from %s for archiving." % 
                                (datafile.filename, replica.url),
                                exc_info=True)
                    nos_errors += 1
                    continue

                fdst.flush()
                arcname = '%s/%s/%s' % (exp.id, datafile.dataset.id,
                                        datafile.filename)
                tf.add(fdst.name, arcname=arcname)
                nos_files += 1
            finally:
                fdst.close()
                if f:
                    f.close()
        tf.close()
        size = long(outfile.tell())
        outfile.close()
        # (The intention is to do these checks as we are writing the archive)
        if minSize or maxSize:
            if minSize and size < minSize:
                raise ArchivingError('Archive for experiment %s is too small' %
                                     exp.id)
            if maxSize and size > maxSize:
                raise ArchivingError('Archive for experiment %s is too big' %
                                     exp.id)
        if exp.url:
            experiment_url = exp.url
        else:
            experiment_url = urljoin(settings.DEFAULT_EXPERIMENT_URL_BASE, 
                                     str(exp.id))
        owner = User.objects.get(id=exp.created_by.id).username
        return Archive(experiment=exp,
                       experiment_title=exp.title,
                       experiment_owner=owner,
                       experiment_url=experiment_url,
                       archive_url=None,
                       size=size, 
                       nos_files=nos_files, 
                       nos_errors=nos_errors,
                       mimetype='application/x-tar', 
                       encoding='x-gzip',
                       sha512sum='')

def last_experiment_change(exp):
    # FIXME - there doesn't appear to be any way to tell when experiment
    # dataset or datafile parameters are added or modified.
    latest = exp.update_time
    for ds in Dataset.objects.filter(experiments=exp):
        for df in Dataset_File.objects.filter(dataset=ds):
            if df.modification_time:
                if latest < df.modification_time:
                    latest = df.modification_time
            elif df.created_time and latest < df.created_time:
                latest = df.created_time

    return latest

def remove_experiment(exp):
    """Completely remove an Experiment, together with any Datasets,
    Datafiles and Replicas that belong to it exclusively.
    """
    for ds in Dataset.objects.filter(experiments=exp):
        if ds.experiments.count() == 1:
            for df in Dataset_File.objects.filter(dataset=ds):
                replicas = Replica.objects.filter(datafile=df, 
                                                  location__type='online')
                for replica in replicas:
                    location = Location.get_location(replica.location.name)
                    location.provider.remove_file(replica.url)
            ds.delete()
        else:
            ds.experiments.remove(exp)
    exp.delete()
    pass

def remove_experiment_data(exp, archive_url, archive_location):
    """Remove the online Replicas for an Experiment that are not shared with
    other Experiments.  When Replicas are removed, they are replaced with
    offline replicas whose 'url' consists of the archive_url, with the 
    archive pathname for the datafile as a url fragment id.
    """
    for ds in Dataset.objects.filter(experiments=exp):
        if ds.experiments.count() == 1:
            for df in Dataset_File.objects.filter(dataset=ds):
                replicas = Replica.objects.filter(datafile=df, 
                                                  location__type='online')
                if replicas.count() > 0:
                    for replica in replicas:
                        location = Location.get_location(replica.location.name)
                        location.provider.remove_file(replica.url)
                        if archive_url:
                            old_replica = replicas[0]
                            path_in_archive = '%s/%s/%s' % (
                                exp.id, ds.id, df.filename)
                            new_replica_url = '%s#%s' % (
                                archive_url, quote(path_in_archive))
                            new_replica = Replica(datafile=old_replica.datafile,
                                                  url=new_replica_url,
                                                  protocol=old_replica.protocol,
                                                  verified=True,
                                                  stay_remote=False,
                                                  location=archive_location)
                            new_replica.save()
                    replicas.delete()
                            
def save_archive_record(archive, url_base):
    """Save an Archive record"""

    archive.archive_url='http://example.com'
    archive.save()
    archive.archive_url = urljoin(
        url_base, '%s-%s-archive.tar.gz' % (archive.experiment.id, archive.id))
    archive.save()
    return archive
