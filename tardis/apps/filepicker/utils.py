'''
taken from https://raw.github.com/Filepicker/django-filepicker/master/django_filepicker/utils.py on 11 Apr 2013
'''
import os
import re
import urllib

from django.core.files import File


class FilepickerFile(object):
    filepicker_url_regex = re.compile(
            r'https?:\/\/www\.filepicker\.io\/api\/file\/.*')

    def __init__(self, url):
        if not self.filepicker_url_regex.match(url):
            raise ValueError('Not a filepicker.io URL: %s' % url)
        self.url = url

    def get_file(self):
        '''
        Downloads the file from filepicker.io and returns a
        Django File wrapper object
        '''
        # clean up any old downloads that are still hanging around
        self.cleanup()

        # The temporary file will be created in a directory set by the
        # environment (TEMP_DIR, TEMP or TMP)
        self.filename, header = urllib.urlretrieve(self.url)
        name = os.path.basename(self.filename)
        disposition = header.get('Content-Disposition')
        if disposition:
            name = disposition.rpartition("filename=")[2].strip('" ')
        filename = header.get('X-File-Name')
        if filename:
            name = filename

        with open(self.filename, 'r') as self.tempfile:
            return File(self.tempfile, name=name)

    def cleanup(self):
        '''
        Removes any downloaded objects and closes open files.
        '''
        if hasattr(self, 'tempfile'):
            self.tempfile.close()
            delattr(self, 'tempfile')

        if hasattr(self, 'filename'):
            # the file might have been moved in the meantime so
            # check first
            if os.path.exists(self.filename):
                os.remove(self.filename)
            delattr(self, 'filename')

    def __enter__(self):
        '''
        Allow FilepickerFile to be used as a context manager as such:

            with FilepickerFile(url) as f:
                model.field.save(f.name, f.)
        '''
        return self.get_file()

    def __exit__(self, *args):
        self.cleanup()

    def __del__(self):
        self.cleanup()
