:mod:`~tardis.tardis_portal.download` -- Downloading of datasets and experiments
================================================================================

.. _ref-download:

.. module:: tardis.tardis_portal.download
.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>


.. autofunction:: download_datafile
.. autofunction:: download_experiment
.. autofunction:: download_datafiles


Writing a Custom Download Provider
==================================

If you need to provide your own download provider - a common example
is storing files on a remote system - you can do do by defining a
custom download provider module. You'll need the following steps.

1. You need to define on your protocol. Files stored on your own
storage system must have the protocol field set and the url must start
with the protocol. Example::

  Dataset_File(dataset=dataset,
               filename='file.txt',
	       url='protocol:///path/to/file.txt',
	       size='1024',
	       protocol='protocol')

2. Your download module needs to provide the following three
hooks:

  * ``def download_datafile(request, datafile_id)``
  * ``def download_experiment(request, experiment_id)``
  * ``def download_datafiles(request)`` which needs to be able to
    retrieve a list of dataset and datafile for download::

      datasets = request.POST.getlist('dataset')
      datafiles = request.POST.getlist('datafile')

These three functions need to be able to access the your file storage
and shoukd return a HttpResponse which either redirects to the file or
contains a file object::

  wrapper = FileWrapper(file('/path/to/file.txt'))
  response = HttpResponse(wrapper, mimetype=datafile.get_mimetype())
  response['Content-Disposition'] = \
                    'attachment; filename="%s"' % datafile.filename
  return response

3. These three views must have url patterns associated in your
*URLconf* module (probably *urls.py*)::

  (r'^datafile/(?P<datafile_id>\d+)/$', 'your.module.download_datafile'),
  (r'^experiment/(?P<experiment_id>\d+)/$', 'your.module.download_experiment'),
  (r'^datafiles/$', 'your.module.download_datafiles'),

4. Settings

In the *settings.py* download providers are activated by specifying them
within the **DOWNLOAD_PROVIDERS** variable::

   DOWNLOAD_PROVIDERS = (
   ('protocol', 'your.module',),
   )
