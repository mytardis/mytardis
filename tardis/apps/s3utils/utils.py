"""
Utilities for S3 objects
"""
from django.conf import settings

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
    import boto3
    from botocore.client import Config

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
        Params = {
            'Bucket': bucket_name,
            'Key': dfo.uri
        },
        ExpiresIn=expiry)
