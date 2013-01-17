# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
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
from django.core.exceptions import SuspiciousOperation

"""
staging.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu.au>

"""

import logging
import shutil
from urllib2 import build_opener
from os import path, makedirs, listdir, rmdir
import posixpath

from django.conf import settings


logger = logging.getLogger(__name__)

def get_dataset_path(dataset):
    return path.join(str(dataset.get_first_experiment().id),
                     str(dataset.id))

def staging_traverse(staging=settings.STAGING_PATH):
    """Recurse through directories and form HTML list tree for jtree

    :param staging: the path to begin traversing
    :type staging: string
    :rtype: string
    """

    ul = '<ul><li id="phtml_1"><a>My Files</a><ul>'

    filelist = []
    try:
        filelist = listdir(staging)
        filelist.sort()
    except OSError:
        logger.error('staging directory doesnt exist' +\
            str(staging))
    for f in filelist:
        ul = ul + traverse(path.join(staging, f), staging)
    return ul + '</ul></li></ul>'


def traverse(pathname, dirname=settings.STAGING_PATH):
    """Traverse a path and return an alphabetically by filename
    sorted nested group of
    unordered (<ul>) list HTML tags::

       <ul>
         <li id="dir2/file2"><a>file2</a></li>
         <li id="dir2/file3"><a>file3</a></li>
         <li id="dir2/subdir"><a>subdir</a>
           <ul>
             <li id="dir2/subdir/file4"><a>file4</a></li>
           </ul>
         </li>
       </ul>

    :param pathname: the directory to traverse
    :type pathname: string
    :param dirname: the root directory of the traversal
    :type dirname: string
    :rtype: string
    """
    if path.isdir(pathname):
        li = '<li id="%s"><a>%s</a>' % (path.relpath(pathname, dirname),
                                    path.basename(pathname))
    else:
        li = '<li class="fileicon" id="%s"><a>%s</a>' % (path.relpath(pathname, dirname),
                                    path.basename(pathname))

    if posixpath.basename(pathname).startswith('.'):
        return ''
    if path.isfile(pathname):
        return li + '</li>'
    if path.isdir(pathname):
        ul = '<ul>'
        filelist = listdir(pathname)
        filelist.sort()
        for f in filelist:
            ul = ul + traverse(path.join(pathname, f), dirname)
        return li + ul + '</ul></li>'
    return ''


class StagingHook():
    __name__ = 'StagingHook'

    def __init__(self, staging=None, store=None):
        self.staging = staging or settings.STAGING_PATH
        self.store = store or settings.FILE_STORE_PATH

    def __call__(self, sender, **kwargs):
        """
        post save callback

        sender
            The model class.
        instance
            The actual instance being saved.
        created
            A boolean; True if a new record was created.
        """
        instance = kwargs.get('instance')
        created = kwargs.get('created')
        if not created:
            # Don't extract on edit
            return
        if not instance.protocol == "staging":
            return
        stage_replica(instance)


def stage_replica(replica):
    from django.core.files.uploadedfile import TemporaryUploadedFile
    with TemporaryUploadedFile(replica.datafile.filename, 
                               None, None, None) as tf:
        if replica.verify(tempfile=tf.file):
            tf.file.flush()
            replica.url = write_uploaded_file_to_dataset(\
                replica.datafile.dataset, tf)
            replica.protocol = ''
            replica.location = Location.get_default_location()
            replica.save()
            return True
        else:
            return False

def get_sync_location():
    from tardis.tardis_portal.models import Location
    return Location.get_location('sync')

def get_sync_root(prefix = ''):
    from uuid import uuid4 as uuid
    def get_candidate_path():
        return path.join(settings.SYNC_TEMP_PATH, prefix + str(uuid()))
    root = (p for p in iter(get_candidate_path,'') if not path.exists(p)).next()
    makedirs(root)
    return root


def get_sync_url_and_protocol(sync_path, filepath):
    from urlparse import urlparse
    from django.utils import _os
    urlObj = urlparse(filepath)
    if urlObj.scheme == '':
        return ('file://'+_os.safe_join(sync_path, filepath), '')
    else:
        return (filepath, urlObj.scheme)


def get_staging_url_and_size(username, filepath):
    '''
    Returns a file:// URL and the size of the file.
    '''
    from os.path import getsize
    from django.utils import _os
    staging_path = get_full_staging_path(username)
    # Safe join should throw exception if filepath is unsafe
    filepath = _os.safe_join(staging_path, filepath)
    return ('file://'+filepath, getsize(filepath))


def get_staging_path():
    """
    return the path to the staging directory
    """
    return settings.STAGING_PATH


def write_uploaded_file_to_dataset(dataset, uploaded_file_post):
    """
    Writes file POST data to the dataset directory in the file store

    :param dataset: dataset whose directory to be written to
    :type dataset: models.Model
    :param uploaded_file_post: uploaded file (either UploadedFile or File)
    :type uploaded_file_post: types.FileType
    :rtype: the path of the file written to
    """

    filename = uploaded_file_post.name

    from django.core.files.storage import default_storage

    # Path on disk can contain subdirectories - but if the request gets 
    # tricky with "../" or "/var" or something we strip them out..
    try:
        copyto = path.join(get_dataset_path(dataset), filename)
        default_storage.path(copyto)
    except (SuspiciousOperation, ValueError):
        copyto = path.join(get_dataset_path(dataset), path.basename(filename))

    logger.debug("Writing uploaded file %s" % copyto)

    realcopyto = default_storage.save(copyto, uploaded_file_post)

    if copyto != realcopyto:
        logger.debug("Actually wrote uploaded file to %s" % copyto)

    return realcopyto


def get_full_staging_path(username):
    # check if the user is authenticated using the deployment's staging protocol
    try:
        from tardis.tardis_portal.models import UserAuthentication
        userAuth = UserAuthentication.objects.get(
            userProfile__user__username=username,
            authenticationMethod=settings.STAGING_PROTOCOL)
    except UserAuthentication.DoesNotExist:
        return None

    from os import path
    staging_path = path.join(settings.STAGING_PATH, username)
    logger.debug('full staging path returned as ' + str(staging_path))
    if not path.exists(staging_path):
        return None
    else:
        return staging_path
