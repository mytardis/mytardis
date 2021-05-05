"""
Utilities for S3 objects
"""
import re
import subprocess
import sys

from django.conf import settings

import boto3
from botocore.client import Config

from . import default_settings


def generate_presigned_url(dfo, expiry=None):
    """
    Generate a presigned URL for an S3 object

    boto3 must be installed if you are using the
    storages.backends.s3boto3.S3Boto3Storage
    storage class, defined in the django-storages package

    Parameters
    ----------
    dfo : DataFileObject
        The DataFileObject to generate the pre-signed URL for
    expiry : int
        The signed URL's expiry in seconds

    Returns
    -------
    string
        The pre-signed URL
    """
    box = dfo.storage_box
    endpoint_url = box.options.get(key='endpoint_url').value
    access_key = box.options.get(key='access_key').value
    secret_key = box.options.get(key='secret_key').value
    bucket_name = box.options.get(key='bucket_name').value
    if not expiry:
        expiry = getattr(
            settings, 'S3_SIGNED_URL_EXPIRY',
            default_settings.S3_SIGNED_URL_EXPIRY)
    s3client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url,
        config=Config(signature_version='s3'))
    return s3client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket_name,
            'Key': dfo.uri
        },
        ExpiresIn=expiry)


def calculate_checksums(dfo, compute_md5=True, compute_sha512=False):
    """Calculates checksums for an S3 DataFileObject instance.
    For files in S3, using the django-storages abstraction is
    inefficient - we end up with a clash of chunking algorithms
    between the download from S3 and MyTardis's Python-based checksum
    calculation.  So for S3 files, we calculate checksums using external
    binaries (md5sum and shasum) instead.

    :param dfo : The DataFileObject instance
    :type dfo: DataFileObject
    :param compute_md5: whether to compute md5 default=True
    :type compute_md5: bool
    :param compute_sha512: whether to compute sha512, default=True
    :type compute_sha512: bool

    :return: the checksums as {'md5sum': result, 'sha512sum': result}
    :rtype: dict
    """
    from botocore.client import Config
    options = dfo.storage_box.options.all()
    boto3_kwargs = dict(config=Config())
    for option in options:
        key = option.key
        if key == 'signature_version':
            boto3_kwargs['config'] = Config(signature_version=option.value)
            continue
        key = key.replace('access_key', 'aws_access_key_id')
        key = key.replace('secret_key', 'aws_secret_access_key')
        if key not in [
                'region_name', 'api_version', 'use_ssl', 'verify',
                'endpoint_url', 'aws_access_key_id', 'aws_secret_access_key',
                'aws_session_token']:
            continue
        boto3_kwargs[key] = option.value
    s3resource = boto3.resource('s3', **boto3_kwargs)
    bucket = s3resource.Bucket(options.get(key='bucket_name').value)

    checksums = {}

    if compute_md5:
        md5sum_binary = 'md5sum'
        if sys.platform == 'darwin':
            md5sum_binary = 'md5'
        with subprocess.Popen(
            [md5sum_binary],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE) as proc:
            bucket.download_fileobj(dfo.uri, proc.stdin)
            stdout, _ = proc.communicate()
        checksums['md5sum'] = \
            re.match(b'\w+', stdout).group(0).decode('utf8')

    if compute_sha512:
        shasum_binary = 'shasum'
        with subprocess.Popen(
            [shasum_binary, '-a', '512'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE) as proc:
            bucket.download_fileobj(dfo.uri, proc.stdin)
            stdout, _ = proc.communicate()
        checksums['sha512sum'] = \
            re.match(b'\w+', stdout).group(0).decode('utf8')

    return checksums
