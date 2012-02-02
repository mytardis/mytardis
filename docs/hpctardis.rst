============
Introduction
============

HPCTardis includes two main components: a set of scripts to be deployed on
HPC facilities, and a customized and extended version of the myTardis system 
that adds metadata extraction and ANDS publishing. 


The diagram below shows the major components of a HPCTardis installation

.. image:: images/hpc_architecture.png



===============
Facility Script
===============

Here is a description of the architecture underlying the facility script

Explain how to setup a user account to connect to the script at the tardis end?


The Facility Script:

* Frameworks 

* Methodologies



==================
HPCTardis/MyTardis
==================

The myTardis architecture, framework and methodology is described in detail in  
:ref:`architecture`

We now describe the key additional features of the HPCTardis system: experiment transfer, metadata extraction and ANDS publishing.

Experiment Transfer Protocol
============================

Here we describe the interaction protocol for experiements into HPCtardis


Metadata Extraction
===================

The metadata extraction function analyses datafiles from experiments in HPCTardis
and creates domain specific parameters.  

 
Configuration
-------------

This system is controlled specifically by ``tardis/apps/hpctardis/metadata.py``

This package provides

* an engine for matching and extracting metadata.

* A set of utility functions for extracting specific forms of metadata

* A ruleset data structure to express mappings from datafiles to executions of utility functions and general python code to extract metadata




Extraction Engine
`````````````````

There are number of different scenarios for metadata extraction in hpctardis

* The Create Experiment Page

  When the user creates a new experiment, the metadata extraction engine is run on each file in each data set individually.
    
* The Edit Experiment Page

  For new files added, extraction will be repeated.  However, existing extracted and edited metadata will not be altered.

* Facility Protocol Extraction

  The facility protocol triggers metadata on recieved data at a dataset level.

* Manual editing

  Through the edit metadata buttons in the view experiment page, individual
   metadata values may be added or edited.

* Management Command

  These commands reextract metadata and overwrites any existing metadata values and any local changes.

  Reextracts metadata for specific experiment::

     bin/django extractmetadata experimentnumber

  Reextract metadata for ALL experiments. Use with caution!::

     bin/django extractmetadata all


The rulesets
````````````

The list data structure ``tardis.apps.hpctardis.metadata.ruleset`` defines all available extraction rules
for a deployment.  The initial package provides a basic set of rules 
for extracting metadata from VASP,SIESTA,GULP,CRYSTAL simulation packages.
However, these rules are incomplete and should form as basis for site specific
customisation of these rules to specific researcher groups.

THe Grammar for the ``rulset`` is as follows::

  ruleset = [RULESET,
          RULESET,
          ...]

  RULEST = (SCHEMA_NS, SCHEMA_NAME):RULES

  RULES = [RULE,RULE,...]

  RULE = (RULENAME,(DATAFILE_REGEX,), EXTRACTRULE)

  RULENAME = string of the metadata parameter name
  
  DATAFILE_REGEX= string python regex for matching datafile names in current dataset.
  
  EXTRACTRULE = string python expression which returns a tuple of (value, unit)
  This rule can contain builtin python functions as well as one or more of the HPCTardis
  utility functions.

The first time the metadata extraction engine is run, then schemas undering the parameter sets
are created in hpctardis and these schemas are used from then onwards for all subsequent extractions.  
To change an existing ruleset, then specific schema would have to be edited or deleted from the
admin tool to be recreated with the new rules 
 
The parameters created by these rules are one of two Tardis types STRING and NUMERIC
The choice is context dependent, if the extracted value can be parsed as number, the resulting
parameter will be NUMERIC, else it will be STRING.


.. seealso::

   ``tardis.apps.hpctardis.metadata.ruleset`` in the basic installation for example
   annotated ruleset examples
                 
Ruleset auxilery functions
``````````````````````````

The ``EXTRACTRULE`` in the ruleset grammer above is a python expression return a
tuple of value string and unit string.  This python expression can contain standard
python builtin functions and operators.  However, for the standard set of definitions
we provide a set of resuable functions useful for extracting metadata files.  
Additional functions can be written using these as a guide.

The key input is a context variable, which contains information such as experiment
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

An experiment can be be in two states: private and public:

*  A private experiment is accessible only to the owner of the experiment unless additional experiment ACLs are created (see :ref:`ref-authframework`)

* A public experiment is accessable for read only access to authorised and external 
  access for experiment metadata.   If ``settings.PRIVATE_DATAFILES`` is ``True``, then 
  download permission for experiments and datafiles is also disabled and redirected
  to contact page.  Furthermore public experiments and associated party and activity
  links are accessable at http://127.0.0.1/rif_cs for direct ingestion of the RIF_CS XML.  

An experiment is made public through the publish_experiment function into 
the experiment detail page.  An experiment goes through a number of steps to become public:

* Owner must acknowledge legal agreement and select at LEAST one of available activity records.  They may also choose to associate any party records and their relation.

* For each selected activity the system looks for a party record associated with it through 'ManagedBy' relation.  The email location field for that person is queried and an email is sent to this email address.

* The authoriser selects the validation link in the received email.

* When all authorising parties have acknowledged then the experiment is made public and records are created in the RIF-CS feed.
 
 
 
Implementation Notes
--------------------

The ``tardis.apps.hpctardis.publish`` package handles aspects of publishing in HPCTardis.

* ``tardis.apps.hpctardis.publish.rif_cs_profile.profiles.default.xml`` is the default template for rending collection records in HPCTardis.  Edit as needed.

* ``tardis.apps.hpctardis.publish.rif_cs_profile.rif_cs.xml`` is the template for rending RIF_CS, specifically party and activity records in HPCTardis.  Edit as needed.

The state of the publishing of an experiment handled by the ``PublishAuthorisation`` model, accesible via the admin tool.  

Activity and Party records are created using the admin tool.

To restore an experiment to private from public, change the flag in the ``Experiment`` model.


Management Commands
-------------------

Resend any outstanding validation emails for an experiment::

   bin/django publish resent experimentnumber

Check all validation requests and if all have been approved, promote experiment to public::

   bin/django publish promote experimentnumber
   
This command is useful after changing status of experiment in PublishAuthorisation model using the admin tool.
For example, to manually authorise an experiment without email, edit the corresponding
entry PublishAuthorisations to APPROVAL state, then this command will set the public
state for the experiment.
   

.. seealso::

   url
      url desc

