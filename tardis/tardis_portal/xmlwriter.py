# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
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
import logging
import os

from django.conf import settings

from .shortcuts import render_to_file

logger = logging.getLogger(__name__)

"""
XML Writer

A set of static methods for writing xml files.

.. moduleauthor:: Steve Androulakis <steve.androulakis@monash.edu>

"""


class XMLWriter:

    @staticmethod
    def write_template_to_dir(dest_dir, dest_filename, template_path, context):
        """
        :param dest_dir: The directory to store the resulting document in
        :type dest_dir: string
        :param dest_filename: The name of the file to be output
        :type dest_filename: string
        :param template_path: The relative path to the Django template to be \
            rendered
        :type template_path: string
        :param context: The Context object (dictionary of variables for \
            template output)
        :type context: :class:`django.template.context.Context`

        :returns: The full path to the created file
        :rtype: string
        """
        filename = os.path.join(dest_dir, dest_filename)
        render_to_file(template_path, filename, context)
        return filename

    @staticmethod
    def write_template_to_file(prefix_dir,
        objectprefix,
        uniqueid,
        templatepath,
        context):
        """
        :param prefix_dir: The subdirectory off of the OAI_DOCS_PATH to store \
            the resulting document in
        :type prefix_dir: string
        :param objectprefix: The name prefix of the resulting file. Files are \
            output in the format prefix-uniqueid.xml
        :type objectprefix: string
        :param uniqueid: The unique ID of the file to be output
        :type uniqueid: string
        :param templatepath: The relative path to the Django template to be \
            rendered
        :type templatepath: string
        :param context: The Context object (dictionary of variables for \
            template output)
        :type context: :class:`django.template.context.Context`

        :returns: The full path to the created file
        :rtype: string
        """

        filename = settings.OAI_DOCS_PATH + os.path.sep + prefix_dir + \
            os.path.sep + str(objectprefix) + "-" + str(uniqueid) + ".xml"

        render_to_file(templatepath,
            filename, context)

        return filename

    @staticmethod
    def write_xml_to_file(prefix_dir,
            objectprefix,
            uniqueid,
            xmlstring):
        """
        :param prefix_dir: The subdirectory off of the OAI_DOCS_PATH to store
            the resulting document in
        :type prefix_dir: string
        :param objectprefix: The name prefix of the resulting file. Files are
            output in the format prefix-uniqueid.xml
        :type objectprefix: string
        :param uniqueid: The unique ID of the file to be output
        :type uniqueid: string
        :param xmlstring: The relative path to the Django template to be
            rendered
        :type xmlstring: string
        :returns: The full path to the created file
        :rtype: string
        """

        filename = settings.OAI_DOCS_PATH + os.path.sep + prefix_dir + \
            os.path.sep + str(objectprefix) + "-" + \
            uniqueid + ".xml"

        with open(filename, "w") as f:
            f.write(xmlstring.encode('UTF-8'))
            f.close()
        return filename
