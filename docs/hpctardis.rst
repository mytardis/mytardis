============
Introduction
============

HPCTardis includes two main components: a set of scripts to be deployed on
HPC facilities, and a customized and extended version of the myTardis system 
that adds metadata extraction and ANDS publishing functionality 


The diagram below shows the major components of a HPCTardis installation

.. image:: images/hpc_architecture.png



===============
Facility Script
===============

**Under Construction**

Here is a description of the architecture underlying the facility script

Explain how to setup a user account to connect to the script at the tardis end?


The Facility Script:

* Frameworks 

* Methodologies


==================
HPCTardis/MyTardis
==================

The MyTardis architecture, framework and methodology is described in detail in  
:ref:`architecture`

We now describe the key additional features of the HPCTardis system: experiment transfer, metadata extraction and ANDS publishing.

Experiment Transfer Protocol
============================

**Under Construction**

Here we describe the interaction protocol for experiements into HPCtardis


Metadata Extraction
===================

The metadata extraction function analyses datafiles from experiments
and extracts domain specific parameter sets according to package specific schemas.
See :ref:`overview` for more details.

 
Configuration
-------------

This system is controlled specifically by ``tardis/apps/hpctardis/metadata.py``

This package provides

* an engine for matching and extracting metadata.

* a set of utility functions for extracting specific forms of metadata.

* a ruleset data structure to express mappings from datafiles to executions of utility functions and general python code to extract metadata.




Extraction Engine
`````````````````

There are number of different scenarios for metadata extraction in hpctardis handled by this engine:

* The *Create Experiment* Page

  When the user creates a new experiment, the metadata extraction engine is run on each file in each data set individually.
    
* The *Edit Experiment* Page

  For new files added to an existing experiment, extraction will be repeated.  However, existing extracted and edited metadata will not be altered.

* Extraction on ingestion from facility

  The facility protocol triggers metadata on recieved data at a dataset level.

* Manual editing

  By using the edit/add metadata buttons in the *view experiment* page, individual metadata entries may be added or edited.

* Management Command

  These shell-level commands reextract metadata and overwrite any existing metadata values and any local changes made by the user.

  Reextract metadata for specific experiment::

     bin/django extractmetadata experimentnumber

  Reextract metadata for ALL experiments. Use with caution!::

     bin/django extractmetadata all


The Rulesets
````````````

The list data structure ``tardis.apps.hpctardis.metadata.ruleset`` defines all available metadata extraction rules
for a deployment.  The initial package provides a basic set of rules 
for extracting metadata from VASP, SIESTA, GULP, CRYSTAL simulation packages.

*Note that these rules are not defintive for these package and should only form a basis for site specific
customisation to requirements of specific researcher groups.*

The Grammar for the ``rulset`` is as follows::

  ruleset = [RULESET,
          RULESET,
          ...]

  RULEST = (SCHEMA_NS, SCHEMA_NAME):RULES

  RULES = [RULE,RULE,...]

  RULE = (RULENAME,(DATAFILE_REGEX,), EXTRACTRULE)

  RULENAME = the metadata parameter name
  
  DATAFILE_REGEX= the python regex for triggering datafile names in current dataset for the rule
  
  EXTRACTRULE = string of python expression which should return a tuple of ``(value, unit)``.
  This rule can contain builtin python functions as well as one or more of the HPCTardis
  utility functions to extract required metaata from datafiles.

The first time the metadata extraction engine is run and rules are triggered, then schemas for the parameter sets
are created in hpctardis and these schemas are used from then onwards for all subsequent extractions.  
To change an existing ruleset, then specific schema would have to be edited or deleted from the
admin tool. 
 
The parameter values created by these rules are strings in the ``EXTRACTRULE``, however are interpreted in Tardis of one of two types: STRING and NUMERIC
The choice context dependent, such that if the extracted value can be parsed as number, the resulting
parameter will be NUMERIC, else it will be STRING in HPCTardis.


.. seealso::

   ``tardis.apps.hpctardis.metadata.ruleset`` in the basic installation for example
   annotated ruleset examples
                 
Ruleset auxilery functions
``````````````````````````

The ``EXTRACTRULE`` in the ruleset grammer above is a python expression that returns a
tuple of value string and unit string.  This python expression can contain standard
python builtin functions and operators.  However, for the standard set of definitions
we provide a set of resuable functions useful for extracting metadata files.  
Additional functions can be written using these as a guide.

The key argument to auxilery fuctions is the *context* parameter, which bundles information such as experiment
number and file matching regex.  See ``tardis.apps.hpctardis.metadata._process_datafiles.data_context``
for more information. 

.. autofunction:: tardis.apps.hpctardis.metadata.get_file_line
.. autofunction:: tardis.apps.hpctardis.metadata.get_file_lines
.. autofunction:: tardis.apps.hpctardis.metadata.get_file_regex
.. autofunction:: tardis.apps.hpctardis.metadata.get_file_regex_all
.. autofunction:: tardis.apps.hpctardis.metadata.get_regex_lines
.. autofunction:: tardis.apps.hpctardis.metadata.get_regex_lines_vallist
.. autofunction:: tardis.apps.hpctardis.metadata.get_final_iteration
.. autofunction:: tardis.apps.hpctardis.metadata.get_constant
        
ANDS Publishing
===============

An experiment in hpctardis can be be in two states: *private* and *public*:

*  A private experiment is accessible only to the owner of the experiment unless additional experiment ACLs are created (see :ref:`ref-authframework`)

* A public experiment is enabled for read-only access to authorised and external users to
  experiment metadata.   If ``settings.PRIVATE_DATAFILES`` is ``True``, then 
  download permission for experiments and datafiles is also *disabled* and redirected
  to a contact page.  Otherwise, downloading of datasets is enabled.  
  Furthermore public experiments and associated party and activity
  links are accessable at http://127.0.0.1/rif_cs for direct ingestion of the RIF_CS XML.  

An experiment is made public through the *publish_experiment* page available from the  
the *experiment details* page.  

An experiment goes through a number of steps to become public:

* The owner must acknowledge legal agreement and select at *least* one of available activity records.  They may also choose to associate any party records and their relations.

* For each selected activity the system looks for a party record associated with it through 'ManagedBy' relation.  The email location field for that person is queried and an email is sent to this email address.

* The authoriser selects the validation link in the received email.

* When *all* authorising parties have acknowledged then the experiment is made public and records are created in the RIF-CS feed.
 
 
 
Implementation Notes
--------------------

The ``tardis.apps.hpctardis.publish`` package handles aspects of publishing in HPCTardis.

* ``tardis.apps.hpctardis.publish.rif_cs_profile.profiles.default.xml`` is the default template for rending collection records in HPCTardis.  Edit as needed.

* ``tardis.apps.hpctardis.publish.rif_cs_profile.rif_cs.xml`` is the template for rending RIF_CS, specifically party and activity records in HPCTardis.  Edit as needed.

The state of the publishing of an experiment handled by the ``PublishAuthorisation`` model, accesible via the admin tool.  

Activity, Party and associated relation records are created using the admin tool.

To restore an experiment to private from public, change the flag in the ``Experiment`` model using the admin tool.

Management Commands
-------------------

Resend any outstanding validation emails for an experiment::

   bin/django publish resend experimentnumber

Check all validation requests and if all have been approved, promote experiment to public::

   bin/django publish promote experimentnumber
   
This command is useful after changing status of experiment in PublishAuthorisation model using the admin tool.
For example, to manually authorise an experiment without email, edit the corresponding
entry PublishAuthorisations to APPROVAL state, then this command will set the public
state for the experiment.
   

