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

import shutil
from os import path, makedirs, listdir

from django.conf import settings

from tardis.tardis_portal.models import Dataset_File
from tardis.tardis_portal.logger import logger


def staging_traverse(staging=settings.STAGING_PATH):
    """
    Recurse through directories and form HTML list tree for jtree

    :param staging: the path to begin traversing
    :type staging: string
    :rtype: string
    """

    ul = '<ul><li id="phtml_1"><a>My Files</a><ul>'
    for f in listdir(staging):
        ul = ul + traverse(path.join(staging, f), staging)
    return ul + '</ul></li></ul>'


def traverse(pathname, dirname=settings.STAGING_PATH):
    """
    Traverse a path and return a nested group of unordered list HTML tags::

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

    li = '<li id="%s"><a>%s</a>' % (path.relpath(pathname, dirname),
                                    path.basename(pathname))
    if path.isfile(pathname):
        return li + '</li>'
    if path.isdir(pathname):
        ul = '<ul>'
        for f in listdir(pathname):
            ul = ul + traverse(path.join(pathname, f), dirname)
        return li + ul + '</ul></li>'
    return ''


class StagingHook():

    def __init__(self, user, experimentId, staging=None, store=None):
        self.staging = staging or settings.STAGING_PATH
        self.store = store or settings.FILE_STORE_PATH
        self.user = user
        self.experimentId = experimentId

    def __call__(self, datafile, created=False):
        if created == False:
            return
        stage_files(datafile, self.experimentId, self.staging, self.store)


def stage_files(datafiles,
                experiment_id,
                staging=settings.STAGING_PATH,
                store=settings.FILE_STORE_PATH,
                ):
    """
    move files from the staging area to the dataset.

    :param datafiles: one or more dataset files
    :type datafiles: :class:`tardis.tardis_portal.models.Dataset_File`
    :param experiment_id: the id of the experiment that the datafiles belong to
    :type experiment_id: string or int
    """
    experiment_path = path.join(store, str(experiment_id))
    if not path.exists(experiment_path):
        makedirs(experiment_path)

    if not isinstance(datafiles, list):
        datafiles = [datafiles]
    for datafile in datafiles:
        urlpath = datafile.url.partition('//')[2]
        todir = path.join(experiment_path, path.split(urlpath)[0])
        if not path.exists(todir):
            makedirs(todir)

        copyfrom = path.join(staging, urlpath)  # to be url
        copyto = path.join(experiment_path, urlpath)
        if path.exists(copyto):
            logger.error("can't stage %s destination exists" % copyto)

            # TODO raise error

            continue

        logger.debug('staging file: %s to %s' % (copyfrom, copyto))
        datafile.size = path.getsize(copyfrom)
        datafile.save()
        shutil.move(copyfrom, copyto)


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

    experiment_path = path.join(settings.FILE_STORE_PATH,
                                str(dataset.experiment.id))

    dataset_path = path.join(experiment_path, str(dataset.id))
    urlpath = 'file:/' + filepath[len(experiment_path):]
    filename = urlpath.rpartition('/')[2]

    datafile = Dataset_File(dataset=dataset, filename=filename,
                            url=urlpath, size=size, protocol='')
    datafile.save()

    return datafile
