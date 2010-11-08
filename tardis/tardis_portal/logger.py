#!/usr/bin/env python
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

# $Author$
# $Revision$
# $Date$


import logging.handlers

from django.conf import settings


def init_logging():
    """
    logging facility for tardis
    sends logging output to a disk file
    supports rotation of disk log files
    fallback on console if disk log file cannot be openend

    http://docs.python.org/library/logging.html

    >>> from tardis.tardis_portal.logger import logger
    >>> logger.info('Hello world.')

    """

    logger = logging.getLogger(__name__)
    try:
        logger.setLevel(settings.LOG_LEVEL)
    except AttributeError:
        logger.setLevel(logging.DEBUG)

    hd = None
    try:
        hd = \
            logging.handlers.RotatingFileHandler(settings.LOG_FILENAME,
                maxBytes=1000000, backupCount=5)
    except:
        hd = logging.StreamHandler()

    fm = None
    try:
        fm = logging.Formatter(settings.LOG_FORMAT)
    except AttributeError:
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    hd.setFormatter(fm)
    logger.addHandler(hd)
    return logger


logger = None
if not logger:
    logger = init_logging()
