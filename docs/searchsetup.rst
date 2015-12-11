
======
Setting up Single search
======

Tardis comes with a pluggable single search option which provides users with a search field on
which can take anything from a simple text search to full lucene query syntax and return a list
of matching Experiment, datasets and datafiles.

The single search box uses SOLR, with a haystack frontent, and accordingly requires some setup.
The single search box is disabled by default.

Setting up SOLR
===============
SOLR doesn't work out of the box with MyTardis. It is not currently installed when buildout is run and requires a number of manual steps to get working.

SOLR runs as a Java applet and can be served from any suitable container. We use Tomcat here.

The following are a very simple list of steps that will get everything up and running. It is advisable to follow up with the person responsible for overseeing security policy at your home institution to see if any extra setup is necessary

Tomcat
------

Tomcat 6.0 (tested with the code) can be downloaded from

http://apache.mirror.aussiehq.net.au/tomcat/tomcat-6/v6.0.33/bin/apache-tomcat-6.0.33.tar.gz .

Un-tar the package and move it to some appropriate location. We use /usr/local/tomcat6 in this example. Please talk to your sysadmin for instructions for your home institution.

    tar xfzv apache-tomcat-6.0.18.tar.gz
    sudo mv apache-tomcat-6.0.18/ /usr/local/tomcat6/


SOLR
----

SOLR 1.4.1 (Tested with the code)  can be downloaded from

    http://apache.mirror.aussiehq.net.au//lucene/solr/1.4.1/apache-solr-1.4.1.tgz

Un-tar the package

    tar xfzv solr-2009-04-06.tgz

Install the .war file from the package into the Tomcat webapps/ directory and copy the example solr application into the tomcat solr/ directory

    sudo cp apache-solr-nightly/dist/apache-solr-nightly.war /usr/local/tomcat6/webapps/solr.war
    sudo cp -r apache-solr-nightly/example/solr/ /usr/local/tomcat6/solr/

You will then need a solr configuration file (This is different to the schema.xml file will we be generating later. The schema describes the structure of our index. The SOLR configuration file describes the behaviour of SOLR). A nice cut and paste configuration is as follows.

sudo mkdir  -p /usr/local/tomcat6/conf/Catalina/localhost/
sudo vim /usr/local/tomcat6/conf/Catalina/localhost/solr.xml

Copy and paste the following in solr.xml

    <Context docBase="/usr/local/tomcat6/webapps/solr.war" debug="0" crossContext="true" >
       <Environment name="solr/home" type="java.lang.String" value="/usr/local/tomcat6/solr" override="true" />
    </Context>

Start Tomcat using

    sudo /usr/local/tomcat6/bin/statup.sh

And check that you can access the SOLR admin page at

    http://server.ip:8080/solr/admin

If you can see an admin page then SOLR is running and ready to be configured for use with Haystack.

Django Configuration
====================

Enabling Single Search
----------------------

A list of default settings for Single Search are already in default_settings.py in the MyTardis repository. Single search is enabled by setting the SINGLE_SEARCH_ENABLED option to True.

Other settings are shown below:

HAYSTACK_SITECONF

Points to the location of the search_sites.py file that Haystack looks to for instructions on which models to index. Defaults to 'tardis.search_sites'

HAYSTACK_SEARCH_ENGINE

Haystack supports a range of search backends. This setting specifies which search backend to use. Should always be set to 'solr'. Can be changed but testing has only been done with SOLR.

HAYSTACK_SOLR_URL

The URL of your SOLR server. Default 'http://127.0.0.1:8080/solr'

HAYSTACK_ENABLE_REGISTRATIONS

Whether or not Haystack is allowed to register signals with Django. This will dictate whether Haystack will be able to automatically register newly added models to the search index. Set based on the value of  SINGLE_SEARCH_ENABLED and defaults to False

Creating a Configuration
------------------------

Haystack can automatically generate a SOLR schema file based on the indexes defined in the Haystack indexes file (tardis/tardis_portal/search_indexes.py). The schema file is a description of how items added to the index are processed during indexing, and how they may be searched.

A configuration is generated using the following command from the main directory of a deployed MyTardis checkout:

    ./bin/django build_solr_schema

Pipe this command into a local file, and then copy it to the solr app directory in Tomcat e.g.

    ./bin/django build_solr_schema > schema.xml
    sudo cp schema.xml /usr/local/tomcat6/solr/conf/schema.xml

Each time the schema.xml file is changed, Tomcat should be reset to reload the configuration.

    sudo /usr/local/tomcat6/bin/shutdown.sh && sudo /usr/local/tomcat6/bin/startup.sh

Alternatively, the following command may be sent directly via curl to the SOLR server to tell it to reload its schema file.

    http://your.solr.url:8080/managerreload?path=/solr


Updating Indexes
----------------

Once SOLR is set up, and Single Search is enabled (i.e. the SINGLE_SEARCH_ENABLED option in settings is set to True) Haystack will automatically register the addition of and changes to models and reflect these in the search index. That is, as soon as a new instance of a model is added to the database, or changes are made to an existing isntance, these changes will be searchable.

If you're adding search to an existing deployment of Django then you'll need to manually trigger a rebuild of the indexes (automatic indexing only happens through signals when models are added or changed).

Rebuilding indexes can be done through the Django admin interface. Haystack registers a number of management commands with the Django framework, the import one here being the rebuild_index command. To rebuild, navigate to your checkout and call the following comman

./bin/django rebuild_index

Haystack will then ask you to confirm your decision (Note: Rebuilding will destroy your existing indexes, and will take a while for large datasets, so be sure), and then start rebuilding.


Note: Changes to the structure or properties of models and schemas (as opposed to simple changes to the data contained in isntances of each) is *not* guaranteed to be reflected in the search indexes. Migrations using South might be picked up, but it is usually safest to re-generate the schema file and then rebuild the entire search index after major changes like this. For information about ways to reflect changes to schema, see the following section.


Updating Schema
---------------

SOLR depends on two types of information: Information about the fields of a model, and how they are to be added to the search index (reflected in schema.xml) and the actual data contained in these models which (indexed as documents in the search index). When new data is added or changed, this can easily be reflected in the index. However, the schema.xml file is a static representation of what SOLR expects objects for indexing to look like. If changes are made to the structure of models (e.g. new fields added, field types changed) or data schemas are added, removed or changed, then the static representation of data in schema.xml will differ from the data being passed into SOLR.

Given that the editing of data schemas is a core function of MyTardis, we need a way to update the schema.xml file when changes are made to MyTardis data schemas. This is not supported by default with Haystack, so we have written a small batch script which will check for changes in the schema.xml file generated by the build_solr_schema admin command. If there are changes, it will replace the existing schema.xml file, restart SOLR and then rebuild the indexes from scratch.

The file is located in the utils/ directory of the main repo. Change the paths at the top of the file to match those of your tardis deploment. The SCHEMA_FILE  path should be set to a symlink you've set up from some appropriate location in your main repo to schema.xml file in the solr/conf/ directory.


We recommend using this file as a guide for your own deployment, making any necessary alterations and then running it nightly at a time when there is likely to be little load on the servers running your SOLR and MyTardis instances.

Adding to templates
===================

Single Seach adds a 'search_form' variable to all contexts once enabled and working (it actually does this always but the variable will be set to None when SingleSearch is enabled). This form can be rendered to your main portal template to provide a persistent search box across all views of your tardis deployment. The form returns results in a special search view specifically for search results.

Single Search also adds some extra functionality to a number of the existing templates (specifically the experiment_view.html template and a number of its ajax templates) to add highlighting to results based on search results. Care should be taking if overriding these templates in your own deployment.
