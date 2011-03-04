============
Contributing
============

Development
===========

Source
------

The MyTARDIS project is hosted on Google Code and uses an subversion
repository for source code control.

Creating a Patch with SVN
-------------------------

SVN users who whish to contribute code please checkout a copy of the
current source::

   svn checkout http://mytardis.googlecode.com/svn/trunk/ mytardis-read-only

You'll need to make sure SVN tracks any new files you add using::

   svn add path/to/new/file

Make the patch using::

   svn diff > feature_name_or_bugfix.diff

and then add an issue to the `issue tracker
<http://code.google.com/p/mytardis/issues/list>`_


Generating Documentation
------------------------

Documentation is done in sphinx and can be built using the commands
provided by the sphinx buildout recipe::

   ./bin/sphinxbuilder


Hudson
------

Hudson is a continuous intergration server that is used within the
MyTARDIS development process to help maintain the quality of the
project. Within Hudson we run use the following script to execute the
build and run the tests.

::

   #!/bin/bash
   rm dist/*
   [ -d egg-cache ] || mkdir -p egg-cache
   export PYTHON_EGG_CACHE=`pwd`/egg-cache
   python setup.py clean
   python bootstrap.py
   ./bin/buildout
   ./bin/django-admin.py test --with-xunit --with-coverage --cover-package=tardis.tardis_portal --with-xcoverage
   python setup.py sdist


Enable the Publish JUnit test result report in the Post-Build Actions
section and use specify the nost tests results output::

   nosetest.xml

To enable reporting of the code coverage you'll need to install the
`Hudson Cobertura plugin
<http://wiki.hudson-ci.org/display/HUDSON/Cobertura+Plugin>`_, once
that is installed you can specify the location of the coverage.xml
file::

   **/coverage.xml


.. seealso::

    `Hudson <http://hudson-ci.org/>`_
        Extensible continuous integration server
