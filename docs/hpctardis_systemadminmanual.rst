==============================
System Administration's Manual
==============================

Installation of HPCTardis
=========================


Prerequisites
-------------

Redhat::

   sudo yum install cyrus-sasl-ldap cyrus-sasl-devel openldap-devel libxslt libxslt-devel libxslt-python

Debian/Ubuntu::

   sudo apt-get install libsasl2-dev libldap libldap2-dev libxslt1.1 libxslt1-dev python-libxslt1

Download
--------

To get the current trunk::

   git clone https://code.google.com/p/hpctardis/
   cd hpctardis
   
Building
--------

HPCTARDIS is using the buildout buildsystem to handle dependencies and create the python class path::

   python bootstrap.py
   ./bin/buildout


Testing
-------
   
Run testcases to verify success::

    bin/django test 

Running Development Server
--------------------------

Copy prototypical settings file for local version::

    cp tardis/settings_hpctardis.py tardis/settings.py

If required, modify standard Django ``tardis/settings.py`` file to change database etc.
Documentation in ``settings_hpctardis.py``

The configure HPCTardis for interactive use, modify the file ``bin/django`` and replace::

    djangorecipe.manage.main('tardis.test_settings')
    
with::
    
    djangorecipe.manage.main('tardis.settings')
    
Setup database and initial data::

    bin/django syncdb --migrate --noinput
    
Create admin user::
    
    bin/django createsuperuser
    
Start the development server::

    bin/django runserver

System should now be running at http://127.0.0.1:8000


Common Admin and Maintenance Tasks
==================================

Admin Tool
----------

Admin user can access the django administration tool to do routine database maintenance::

http://127.0.0.1/admin

Management Commands
-------------------

Create a new HPCTardis user::

   bin/django createuser 

Installation of Facility Scripts
================================

venki to do