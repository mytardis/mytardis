"""
Default settings for s3utils app
"""

S3_SIGNED_URL_EXPIRY = 30
"""
A short expiry (30 seconds) is used, because it is only
intended to provide access long enough for an authenticated
MyTardis user to be redirected to the signed URL.
"""
