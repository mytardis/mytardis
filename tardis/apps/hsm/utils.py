# -*- coding: utf-8 -*-
"""HSM utils module.  Utilities for detecting whether files in
Hierarchical Storage Management are online or offline (on tape).
"""
from __future__ import unicode_literals

import errno
import logging
import os

logger = logging.getLogger(__name__)

FILE_ATTRIBUTE_OFFLINE = 0x00001000


def _stat_os(path):
    """Use os.stat to calculate size and block number

    Parameters
    ----------
    path : str
        Path to file to calculate size and block number for

    Returns
    -------
    tuple
        tuple of size and block number i.e., (size, blocks)
    """
    import os
    stats = os.stat(path)
    return stats.st_size, stats.st_blocks


def _stat_subprocess(path):
    """Use subprocess to call underlying stat command. Uses
    regexp to isolate size and block number.

    Parameters
    ----------
    path : str
        Path to file to calculate size and block number for

    Returns
    -------
    tuple
        tuple of size and block number i.e., (size, blocks)
    """
    import subprocess  # nosec - Bandit B404: import_subprocess
    import sys

    format_option = '-f' if sys.platform == 'darwin' else '-c'
    format_string = '%z,%b' if sys.platform == 'darwin' else '%s,%b'
    with subprocess.Popen(  # nosec - Bandit B603: subprocess_without_shell_equals_true
        ['/usr/bin/stat', format_option, format_string, path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
        stdout, _ = proc.communicate()

    return tuple(int(stat) for stat in stdout.split(b','))


def file_is_online(path):  # pylint: disable=R1710
    """Detects whether a file is online or offline (on tape).

    Parameters
    ----------
    path : str
        Path to the file for which we want to determine online/offline status.

    Returns
    -------
    bool
        specifies whether the file in online i.e., not on tape.
    """
    try:
        d_raw = os.getxattr(path, "user.cifs.dosattrib")
        d_int = int.from_bytes(d_raw, byteorder="little")
        if d_int & FILE_ATTRIBUTE_OFFLINE == FILE_ATTRIBUTE_OFFLINE:
            return False
        return True
    except OSError as e:
        if e.errno not in (errno.EPERM, errno.ENOTSUP, errno.ENODATA):
            logger.error('cannot get status for file: %s' % (path,))
