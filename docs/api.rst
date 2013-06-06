==========================
 RESTful API for MyTardis
==========================

The data and metadata stored in MyTardis instances is made accessible through
a RESTful API.

Not all functionality is being implement at the same time. This documentation
reflects what is available and tested.

Accessible Models
=================

- Experiment
- ExperimentParameterSet
- ExperimentParameter
-
- Dataset
- DatasetParameterSet
- DatasetParameter
-
- Dataset_File
- DatafileParameterSet
- DatafileParameter

Creating objects, adding files (POST)
=====================================

The creation of Experiments, Datasets and Dataset_Files via POSTs with the
option to include metadata/parametersets has been implemented and tested.

The following examples demonstrate how to go about it.

In all except the file attachment case the POST data should be a JSON string,
the ``Content-Type`` header needs to be set to ``application/json`` and the
``Accept`` header as well. Other response formats may be made available in the
future.

In all cases the URI of the created object is returned in the ``Location``
header of the response.

Experiments
-----------
Example JSON input::

  {
    "title": "API-created Experiment #1",
    "description": "Wow, all automatic!",
    "institution_name": "Monash University",
    "parameter_sets": [
      {
        "schema": "http://institution.com/my/schema",
        "parameters": [
           {
             "name": "important_parameter_1",
             "value": "Test16"
           },
           {
             "name": "important_parameter_3",
             "value": "57.136"
           }
        ]
      },
      {
        "schema": "http://company.com/some/other/schema",
        "parameters": [
           {
             "name": "meaningful_name",
             "value": "Test17"
           },
           {
             "name": "meaningless_name",
             "value": "1234"
           }
        ]
      }
    ]
  }

This creates an experiment with two parametersets with two parameters each.

Alternative to Schema namespaces and Parameter names, you can also specify the
URIs to each. Until the querying of Schemas and Parameters is documented this
is discouraged.

Datasets
--------
Example JSON input::

  {
    "description": "API-created Dataset",
    "experiments": [
      "/api/v1/experiment/1/",
      "/api/v1/experiment/2/"
    ],
    "immutable": false,
    "parameter_sets": [
      {
        "parameters": [
          {
            "name": "obscure-instrument-setting-52",
            "value": "awesome dataset api POST"
          },
          {
            "name": "temperature",
            "value": "301"
          }
        ],
        "schema": "http://datasets.com/need/schemas/too"
      },
      {
        "parameters": [
          {
            "name": "someotherparameter",
            "value": "some other value"
          }
        ],
        "schema": "http://better-datasets.com/offers/better/schemas"
      }
    ]
  }

Dataset_Files
-------------
There are three ways to add a file to MyTardis via the API.

Via multipart form POST
~~~~~~~~~~~~~~~~~~~~~~~
This works for single files at the moment.

The key is to send a multipart-form instead of 'application/json'. This can be
accomplished with the requests library as shown in the following example.

To use requests you need to install it first, eg. ``pip install requests``.

Also, for this to work, the POST data needs to be sent with the JSON string
called ``'json_data'`` and the file called ``'attached_file'``.

Example JSON input::

  {
      "dataset": "/api/v1/dataset/1/",
      "filename": "mytestfile.txt",
      "md5sum": "c858d6319609d6db3c091b09783c479c",
      "size": "12",
      "mimetype": "text/plain",
      "parameter_sets": [{
          "schema": "http://datafileshop.com/fileinfo/v1",
          "parameters": [{
              "name": "fileparameter1",
              "value": "123"
          },
          {
              "name": "fileparameter2",
              "value": "1234"
          }]
      }]
  }

Example requests script::

    import requests
    from requests.auth import HTTPBasicAuth

    url = "http://localhost:8000/api/v1/dataset_file/"
    headers = {'Accept': 'application/json'}
    response = requests.post(url, data={"json_data": data}, headers=headers,
                             files={'attached_file': open(filename, 'rb')},
                             auth=HTTPBasicAuth(username, password)
                             )


Via staging location
~~~~~~~~~~~~~~~~~~~~

Another way to add a file is to create the database entry first without
providing a storage location. This will return back a location on the server
that you are assumed to have access to. Once the file appears there, for
example when you copy it there, it will be moved to its permanent storage
location managed by MyTardis.

The full file path that you should copy/move the file to is returned as the
content of the response.

Example JSON input::

  {
      "dataset": "/api/v1/dataset/1/",
      "filename": "mytestfile.txt",
      "md5sum": "c858d6319609d6db3c091b09783c479c",
      "size": "12",
      "mimetype": "text/plain",
      "parameter_sets": [{
          "schema": "http://datafileshop.com/fileinfo/v1",
          "parameters": [{
              "name": "fileparameter1",
              "value": "123"
          },
          {
              "name": "fileparameter2",
              "value": "1234"
          }]
      }]
  }



Via shared permanent storage location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method assumes that there exists a storage that is shared between
MyTardis and you. The registered file will remain in this location.

For this to work you need to get a ``Location`` (internal MyTardis settings)
name to submit with your metadata.

Examples JSON::

  {
     "dataset": "/api/v1/dataset/1/",
     "filename": "mytestfile.txt",
     "md5sum": "c858d6319609d6db3c091b09783c479c",
     "size": "12",
     "mimetype": "text/plain",
     "replicas": [{
         "url": "mytestfile.txt",
         "location": "local",
	 "protocol": "file"
     }],
     "parameter_sets": [{
         "schema": "http://datafileshop.com/fileinfo/2",
         "parameters": [{
             "name": "fileparameter1",
             "value": "123"
         },
         {
             "name": "fileparameter2",
             "value": "123"
         }]
     }]
  }

urllib2 POST example script
---------------------------

Replace ``MODEL`` with
one of the available model names in lower case. ``data`` is the JSON as a
string.

::

    import urllib2
    url = "http://localhost:8000/api/v1/MODEL/"
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json'}
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm="django-tastypie",
                              uri=url,
                              user=username,
                              passwd=password)
    opener = urllib2.build_opener(auth_handler)
    urllib2.install_opener(opener)
    myrequest = urllib2.Request(url=url, data=data,
                                headers=headers)
    myrequest.get_method = lambda: 'POST'
    output = "error"
    output = urllib2.urlopen(myrequest)
    print output.headers["Location"]
