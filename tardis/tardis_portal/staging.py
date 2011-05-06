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
import shutil
from os import path, makedirs, listdir, rmdir

from django.conf import settings


logger = logging.getLogger(__name__)


def staging_traverse(staging=settings.STAGING_PATH):
    """Recurse through directories and form HTML list tree for jtree

    :param staging: the path to begin traversing
    :type staging: string
    :rtype: string
    """

    ul = '<ul><li id="phtml_1"><a>My Files</a><ul>'
    filelist = listdir(staging)
    filelist.sort()
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

    if pathname.rpartition('/')[2].startswith('.'):
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
        stage_file(instance)


def stage_file(datafile):
    """move files from the staging area to the dataset.
    treat directories with care.

    :param datafile: a datafile to be staged
    :type datafile: :class:`tardis.tardis_portal.models.Dataset_File`
    """
    dataset_path = datafile.dataset.get_absolute_filepath()
    copyfrom = datafile.url

    relpath = calculate_relative_path(datafile.protocol,
                                      datafile.url)
    copyto = path.join(dataset_path, relpath)
    original_copyto = copyto

    logger.debug('staging file: %s to %s' % (copyfrom, copyto))
    if path.isdir(copyfrom):
        if not path.exists(copyto):
            makedirs(copyto)
    else:
        if path.exists(copyto):
            logger.error("duplicate file: %s . Renaming." % copyto)
            copyto = duplicate_file_check_rename(copyto)
            # TODO raise error

        if not path.exists(path.dirname(copyto)):
            makedirs(path.dirname(copyto))

        shutil.copy(copyfrom, copyto)

    # duplicate file handling
    split_copyto = copyto.rpartition('/')
    filename = split_copyto[2]
    relpath = relpath.rpartition('/')[0]
    if relpath:
        relpath = relpath + path.sep

    datafile.filename = filename
    datafile.url = "tardis://" + relpath + filename
    datafile.protocol = "tardis"
    datafile.size = path.getsize(datafile.get_absolute_filepath())
    datafile.save()

    # rmdir each dir from copyfrom[get_staging_path():] if empty
    # currently doesn't do anything since we're copying and not moving..
    basedir = copyfrom[:-len(relpath)]
    while len(relpath) > 0:
        try:
            rmdir(basedir + relpath)
        except OSError:
            pass
        relpath = path.dirname(relpath)


def get_staging_path():
    """
    return the path to the staging directory
    """
    return settings.STAGING_PATH


def calculate_relative_path(protocol, filepath):
    """return the relative path to the datafile, that is the absolute path
    minus the staging directory information.

    :param protocol: a protocol
    :type protocol: string
    :param url: a url like path
    :type url: string
    """
    if protocol == "staging":
        staging = settings.STAGING_PATH
        rpath = filepath[len(staging)+1:]
        return rpath.partition("/")[2]
    elif protocol == "tardis":
        staging = settings.STAGING_PATH
        rpath = filepath[len(staging)-1:]
        return rpath.lstrip(path.sep)
    else:
        logger.error("the staging path of the file %s is invalid!" % filepath)
        raise ValueError("Unknown protocol, there is no way to calculate a relative url for %s urls." % protocol)

    # if not filepath.startswith(staging):
    #     raise ValueError("filepath %s is either already relative or invalid." % filepath)

def duplicate_file_check_rename(copyto):
    """
    Checks if the destination for the file already exists and returns
    a non-conflicting name

    :param copyto: The destination path to check
    :type copyto: string
    :rtype: The new non-conflicting path (the original path if no conflicts)
    """
    i = 1
    base, filename = path.split(copyto)
    name, ext = path.splitext(filename)
    result = copyto

    while path.exists(result):
        logger.debug('%s destination exists' % result)
        result = path.join(base, "{0}_{1}{2}".format(name, i, ext))
        i += 1
    return result


def write_uploaded_file_to_dataset(dataset, uploaded_file_post):
    """
    Writes file POST data to the dataset directory in the file store

    :param dataset_id: dataset who's directory to be written to
    :type dataset: models.Model
    :rtype: the path of the file written to
    """

    filename = uploaded_file_post.name

    experiment_path = path.join(settings.FILE_STORE_PATH,
                                str(dataset.experiment.id))

    dataset_path = path.join(experiment_path, str(dataset.id))

    if not path.exists(dataset_path):
        makedirs(dataset_path)

    copyto = path.join(dataset_path, filename)

    copyto = duplicate_file_check_rename(copyto)

    uploaded_file = open(copyto, 'wb+')

    for chunk in uploaded_file_post.chunks():
        uploaded_file.write(chunk)

    uploaded_file.close()

    return copyto


def add_datafile_to_dataset(dataset, filepath, size):
    """
    Adds datafile metadata to a dataset

    :param dataset: dataset who's directory to be written to
    :type dataset: :class:`tardis.tardis_portal.models.Dataset`
    :param filepath: The full os path to the file
    :type filepath: string
    :param size: The file size in bytes
    :type size: string
    :rtype: The new datafile object
    """
    from tardis.tardis_portal.models import Dataset_File

    experiment_path = path.join(settings.FILE_STORE_PATH,
                                str(dataset.experiment.id))

    dataset_path = path.join(experiment_path, str(dataset.id))
    urlpath = 'tardis:/' + filepath[len(dataset_path):]
    filename = urlpath.rpartition('/')[2]

    datafile = Dataset_File(dataset=dataset, filename=filename,
                            url=urlpath, size=size, protocol='')
    datafile.save()

    return datafile


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
    return path.join(settings.STAGING_PATH, username)
