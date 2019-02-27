# -*- coding: utf-8 -*-
"""HSM utils module.  Utilities for detecting whether files in
Hierarchical Storage Management are online or offline (on tape).
"""
from __future__ import unicode_literals

from django.conf import settings

from . import default_settings


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
    proc = subprocess.Popen(  # nosec - Bandit B603: subprocess_without_shell_equals_true
        ['/usr/bin/stat', format_option, format_string, path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = proc.communicate()

    return tuple(int(stat) for stat in stdout.split(b','))


def file_is_online(path):
    """Detects whether a file is online or offline (on tape).

    Basically this function checks the size and block number.
    If size > 0 and block number == 0, this is typically a sign that
    files are on tape.

    We attempt to os.stat to determine file size and block number;
    however, this doesn't work on all unix-like systems, so if it fails
    we attempt to determine them using a subprocess proc call to stat
    which we aim to match using a regexp.

    Notes
    -----
    We set a minimum size since very small files can be stored
    in the inode and hence have a 0 blksize.

    Parameters
    ----------
    path : str
        Path to the file for which we want to determine size and and block
        number.

    Returns
    -------
    bool
        specifies whether the file in online i.e., not on tape.
    """
    try:
        size, blocks = _stat_os(path)
    except AttributeError:
        size, blocks = _stat_subprocess(path)

    max_inode_file_size = getattr(
        settings, 'HSM_MAX_INODE_FILE_SIZE',
        default_settings.HSM_MAX_INODE_FILE_SIZE)

    if size > max_inode_file_size and blocks == 0:
        return False
    return True
