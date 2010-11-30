#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
download.py

.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>

"""
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

from tardis.tardis_portal.models import *
from tardis.tardis_portal.views import return_response_not_found, \
    return_response_error, has_datafile_access, experiment_access_required
from tardis.tardis_portal.logger import logger

from os.path import join

import subprocess
import urllib


def download_datafile(request, datafile_id):

    # todo handle missing file, general error
    datafile = Dataset_File.objects.get(pk=datafile_id)

    if has_datafile_access(datafile.id, request.user):
        url = datafile.url

        if url.startswith('http://') or url.startswith('https://') \
            or url.startswith('ftp://'):
            return HttpResponseRedirect(datafile.url)
        else:
            file_path = join(settings.FILE_STORE_PATH,
                             str(datafile.dataset.experiment.id),
                             datafile.url.partition('//')[2])
            try:
                logger.debug(file_path)
                wrapper = FileWrapper(file(file_path))

                response = HttpResponse(wrapper,
                        mimetype='application/octet-stream')
                response['Content-Disposition'] = \
                    'attachment; filename=' + datafile.filename

                # import os
                # response['Content-Length'] = os.path.getsize(file_path)

                return response

            except IOError:
                return return_response_not_found(request)
    else:

        return return_response_error(request)


@experiment_access_required
def download_experiment(request, experiment_id):

    # Create the HttpResponse object with the appropriate headers.
    # TODO: handle no datafile, invalid filename, all http links
    # (tarfile count?)
    experiment = Experiment.objects.get(pk=experiment_id)

    cmd = 'tar -C %s -c %s/' % (settings.FILE_STORE_PATH,
                                str(experiment.id))
    #logger.debug('TAR COMMAND: ' + tar_command)

    response = HttpResponse(FileWrapper(subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            shell=True).stdout),
                            mimetype='application/x-tar')

    response['Content-Disposition'] = 'attachment; filename=experiment' \
        + str(experiment.id) + '-complete.tar'

    # response['Content-Length'] = fileSize + 5120

    return response


def download_datafiles(request):

    # Create the HttpResponse object with the appropriate headers.
    # TODO: handle no datafile, invalid filename, all http links
    # (tarfile count?)
    expid = request.POST['expid']
    protocols = []
    fileString = ''
    fileSize = 0

    if 'datafile' or 'dataset' in request.POST:

        if (len(request.POST.getlist('datafile')) > 0 \
                or len(request.POST.getlist('dataset'))) > 0:

            datasets = request.POST.getlist('dataset')
            datafiles = request.POST.getlist('datafile')

            for dsid in datasets:
                for datafile in Dataset_File.objects.filter(dataset=dsid):
                    if has_datafile_access(datafile.id, request.user):
                        p = datafile.protocol
                        if not p in protocols:
                            protocols += [p]
                        if datafile.url.startswith('file://'):
                            absolute_filename = datafile.url.partition('//')[2]
                            fileString += expid + '/' + absolute_filename + ' '
                            fileSize += long(datafile.size)

            for dfid in datafiles:
                datafile = Dataset_File.objects.get(pk=dfid)
                if datafile.dataset.id in datasets:
                    continue
                if has_datafile_access(dfid, request.user):
                    p = datafile.protocol
                    if not p in protocols:
                        protocols += [p]
                    if datafile.url.startswith('file://'):
                        absolute_filename = datafile.url.partition('//')[2]
                        fileString += expid + '/' + absolute_filename + ' '
                        fileSize += long(datafile.size)

        else:
            return return_response_not_found(request)

    elif 'url' in request.POST:

        if not len(request.POST.getlist('url')) == 0:
            for url in request.POST.getlist('url'):
                datafile = \
                    Dataset_File.objects.get(url=urllib.unquote(url),
                        dataset__experiment__id=request.POST['expid'])
                if has_datafile_access(datafile.id, request.user):
                    p = datafile.protocol
                    if not p in protocols:
                        protocols += [p]
                    if datafile.url.startswith('file://'):
                        absolute_filename = datafile.url.partition('//')[2]
                        fileString += expid + '/' + absolute_filename + ' '
                        fileSize += long(datafile.size)

        else:
            return return_response_not_found(request)
    else:
        return return_response_not_found(request)

    # more than one download location?
    if len(protocols) > 1:
        response = HttpResponseNotFound()
        response.write('<p>Different locations selected!</p>\n')
        response.write('Please limit your selection and try again.\n')
        return response

    # redirect request if download protocol found
    if protocols[0] != '':
        from django.core.urlresolvers import resolve
        view, args, kwargs = resolve('/%s%s' % (protocols[0],
                                                request.path))
        kwargs['request'] = request
        return view(*args, **kwargs)

    else:
        # tarfile class doesn't work on large files being added and
        # streamed on the fly, so going command-line-o
        cmd = 'tar -C %s -c %s' % (settings.FILE_STORE_PATH,
                                   fileString)

        response = \
            HttpResponse(FileWrapper(subprocess.Popen(cmd,
                                                      stdout=subprocess.PIPE,
                                                      shell=True).stdout),
                         mimetype='application/x-tar')
        response['Content-Disposition'] = \
                'attachment; filename=experiment%s.tar' % expid
        response['Content-Length'] = fileSize + 5120
        return response
