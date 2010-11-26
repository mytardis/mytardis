#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
views.py

@author Steve Androulakis
@author Ulrich Felzmann

"""

from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

from tardis.tardis_portal.models import *
from tardis.tardis_portal.views import render_response_index, \
    return_response_not_found, return_response_error, \
    has_datafile_access, experiment_access_required
from tardis.tardis_portal.logger import logger

from os.path import join

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
                from django.core.servers.basehttp import FileWrapper
                wrapper = FileWrapper(file(file_path))

                response = HttpResponse(wrapper,
                        mimetype='application/octet-stream')
                response['Content-Disposition'] = \
                    'attachment; filename="' + datafile.filename + '"'

                # import os
                # response['Content-Length'] = os.path.getsize(file_path)

                return response

            except IOError, io:
                return return_response_not_found(request)
    else:

        return return_response_error(request)


@experiment_access_required
def download_experiment(request, experiment_id):

    # Create the HttpResponse object with the appropriate headers.
    # TODO: handle no datafile, invalid filename, all http links
    # (tarfile count?)

    from django.core.servers.basehttp import FileWrapper

    experiment = Experiment.objects.get(pk=experiment_id)

    tar_command = 'tar -C ' + settings.FILE_STORE_PATH + ' -c ' + \
        str(experiment.id) + '/'
    logger.debug('TAR COMMAND: ' + tar_command)

    import subprocess

    response = HttpResponse(FileWrapper(subprocess.Popen(tar_command,
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
    protocols = []

    if 'datafile' in request.POST:

        if not len(request.POST.getlist('datafile')) == 0:
            from django.utils.safestring import SafeUnicode
            from django.core.servers.basehttp import FileWrapper

            fileString = ''
            fileSize = 0
            for dfid in request.POST.getlist('datafile'):
                datafile = Dataset_File.objects.get(pk=dfid)
                if has_datafile_access(dfid, request.user):
                    p = datafile.protocol
                    if not p in protocols:
                        protocols += [p]
                    if datafile.url.startswith('file://'):
                        absolute_filename = datafile.url.partition('//')[2]
                        fileString + request.POST['expid'] \
                            + '/' + absolute_filename + ' '
                        fileSize = fileSize + long(datafile.size)
            # FIXME
            if len(protocols) > 1:
                return_response_not_found(request)
            # tarfile class doesn't work on large files being added and
            # streamed on the fly, so going command-line-o

            tar_command = 'tar -C ' + settings.FILE_STORE_PATH + ' -c ' \
                + fileString

            import shlex
            import subprocess

            response = \
                HttpResponse(FileWrapper(subprocess.Popen(tar_command,
                             stdout=subprocess.PIPE,
                             shell=True).stdout),
                             mimetype='application/x-tar')
            response['Content-Disposition'] = \
                'attachment; filename=experiment' + \
                request.POST['expid'] + '.tar'
            response['Content-Length'] = fileSize + 5120

            return response

    elif 'url' in request.POST:

        if not len(request.POST.getlist('url')) == 0:
            from django.utils.safestring import SafeUnicode
            from django.core.servers.basehttp import FileWrapper

            fileString = ''
            fileSize = 0
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
                        fileString = fileString + request.POST['expid'] \
                            + '/' + absolute_filename + ' '
                        fileSize = fileSize + long(datafile.size)

            # FIXME
            if len(protocols) > 1:
                return_response_not_found(request)

            # tarfile class doesn't work on large files being added and
            # streamed on the fly, so going command-line-o
            tar_command = 'tar -C ' + settings.FILE_STORE_PATH + ' -c ' + \
                fileString

            response = \
                HttpResponse(FileWrapper(subprocess.Popen(tar_command,
                             stdout=subprocess.PIPE,
                             shell=True).stdout),
                             mimetype='application/x-tar')
            response['Content-Disposition'] = \
                'attachment; filename=experiment' + request.POST['expid'] + \
                '.tar'
            response['Content-Length'] = fileSize + 5120

            return response
        else:
            return return_response_not_found(request)
    else:
        return return_response_not_found(request)
