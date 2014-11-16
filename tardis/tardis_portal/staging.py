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
"""
staging.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu.au>

"""

import logging
import os
from os import path, makedirs, listdir
import posixpath

from django.conf import settings

from tardis.tardis_portal.models.storage import StorageBox

logger = logging.getLogger(__name__)


def get_dataset_path(dataset):
    return dataset.get_path()


def staging_list(pathname=settings.STAGING_PATH,
                 dirname=settings.STAGING_PATH, root=False):
    from django.utils import _os
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
    directory_listing = ''

    # so people aren't malicious with the loading of files in the UI
    if not path.abspath(pathname).startswith(dirname):
        return None

    filelist = listdir(pathname)
    filelist.sort()
    for f in filelist:
        if path.isdir(_os.safe_join(pathname, f)):
            li = '<li class="jstree-closed" id="%s"><a>%s</a>' \
                 % (path.relpath(_os.safe_join(pathname, f), dirname),
                    path.basename(f))
            directory_listing = directory_listing + li + '<ul></ul></li>'
        else:
            if not posixpath.basename(f).startswith('.'):
                li = '<li class="fileicon" id="%s"><a>%s</a>' \
                     % (path.relpath(_os.safe_join(pathname, f), dirname),
                        path.basename(f))
                directory_listing = directory_listing + li + '</li>'

    if root:
        # root call
        directory_listing = '<ul><li id="phtml_1"><a>'\
            + str(path.split(path.dirname(pathname))[1]) \
            + '</a><ul>' \
            + directory_listing \
            + '</ul></li></ul>'

    return directory_listing


def stage_dfo(dfo):
    from django.core.files.uploadedfile import TemporaryUploadedFile
    from tardis.tardis_portal.models import DataFileObject, StorageBox
    if dfo.storage_box.attributes.filter(key="staging", value="True").count() == 0:
        raise ValueError('Only files in staging storage boxes can be staged')
    with TemporaryUploadedFile(dfo.datafile.filename,
                               None, None, None) as tf:
        if dfo.verify(tempfile=tf.file):
            tf.file.flush()
            dfo.storage_box = StorageBox.get_default_storage()
            dfo.uri = None
            dfo.file_object = tf
            logger.debug("dfo.uri = " + dfo.uri)
            dfo.save()
            return True
        else:
            return False


def get_sync_location():
    from tardis.tardis_portal.models import Location
    return Location.get_location('sync')


def get_sync_root(prefix='', sbox=None):
    from uuid import uuid4 as uuid

    if sbox is not None:
        root_path = sbox.options.get(key='location').value
    else:
        boxes = StorageBox.objects.filter(attributes__key="staging",
                                          attributes__value="True")
        if len(boxes) > 0:
            root_path = boxes[0].options.get(key='location').value
        else:
            root_path = settings.STAGING_PATH

    def get_candidate_path():
        return path.join(root_path, prefix + str(uuid()))
    root = (p for p in iter(get_candidate_path, '')
            if not path.exists(p)).next()
    oldmask = os.umask(0o007)
    makedirs(root)
    os.umask(oldmask)
    # chmod seems safer than umask subtraction
    os.chmod(root, 0o2770)
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


def write_uploaded_file_to_dataset(dataset, uploaded_file_post,
                                   subdir=None):
    """
    Broken, now that the storagebox takes care of writing files.
    Writes file POST data to the dataset directory in the file store

    :param dataset: dataset whose directory to be written to
    :type dataset: models.Model
    :param uploaded_file_post: uploaded file (either UploadedFile or File)
    :type uploaded_file_post: types.FileType
    :rtype: the path of the file written to
    """
    raise DeprecationWarning


def get_full_staging_path(username):
    # check if the user is authenticated using the deployment's
    # staging protocol
    try:
        from tardis.tardis_portal.models import UserAuthentication
        UserAuthentication.objects.get(
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
