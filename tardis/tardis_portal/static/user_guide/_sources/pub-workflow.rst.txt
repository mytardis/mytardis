#############################
MyTardis Publication Workflow
#############################

***********
Basic Usage
***********

Listing Existing Publications and Drafts
========================================
Click on "My Publications" in the menu bar to see existing publications and drafts which you have access to:

.. image:: _images/my-publications-draft-saved.png
   :width: 90%

Creating a Draft Publication
============================
From the "My Publications" page, click "Create publication" to begin a draft publication:

.. image:: _images/create-publication.png

The publication form should appear, showing whatever introductory text has
been configured by your MyTardis administrator, using the
``PUBLICATION_INTRODUCTION`` setting in ``tardis/settings.py``:

.. image:: _images/publication-form-introduction.png

After acknowledging the introductory text, you can begin selecting datasets
to include in your publication:

.. image:: _images/pub-form-selecting-datasets.png  

Selected datasets appear on the right:

.. image:: _images/pub-form-selected-dataset.png

You can then describe each included dataset (beyond what is already in the
dataset's description field):

.. image:: _images/pub-form-extra-info.png

The final page allows you to specify the authors, license, acknowledgements and
release date.  **The last page of the form will be split into two pages in the
next version of the publication form.**

.. image:: _images/pub-form-final-page.png

After clicking "Save and finish Later", you can see the publication in the Drafts
section of the "My Publications" page:

.. image:: _images/my-publications-draft-saved.png
   :width: 90%


Resuming a Draft Publication
============================
The "Resume draft" button below opens the publication form, allowing you to make further changes:

.. image:: _images/my-publications-draft-saved.png
   :width: 90%

When resuming a draft, you will be taken straight to the second page of the publication form below,
skipping the introductory text:

.. image:: _images/pub-form-selected-dataset.png


Deleting a Draft Publication
============================
The "Delete draft" button below allowd you to delete a draft publication:

.. image:: _images/my-publications-draft-saved.png
   :width: 90%

You will be asked to confirm that you really want to delete the draft publication:

.. image:: _images/delete-confirmation.png


Minting a DOI (Digital Object Identifier)
=========================================
The "Mint DOI" button below allowd you to mint a DOI (Digital Object Identifier):

.. image:: _images/my-publications-draft-saved.png
   :width: 90%

You will be asked to confirm that you really want to mint a DOI:

.. image:: _images/mint-doi-confirmation.png


Sharing a Draft Publication
============================
The "Share" button below opens temporary links dialog, allowing you grant short-term access (3 months)
to the draft publication via a temporary URL:

.. image:: _images/my-publications-draft-saved.png
   :width: 90%

The first time you click Share, you won't have any tokens for granting temporary access:

.. image:: _images/temporary-links-no-tokens.png

After clicking the "Create New Temporary Link" button, you should see a temporary link:

.. image:: _images/temporary-links-one-token.png  


**********************************
For MyTardis System Administrators
**********************************

Enabling or Disabling the Publication Workflow
==============================================
The publication workflow is enabled by default in a new MyTardis installation:

``tardis/default_settings/apps.py:``

.. code-block:: python

  ...
  INSTALLED_APPS = (
      ...
      'tardis.apps.publication_workflow',
      ...
  )

If necessary, it can be disabled in ``tardis/settings.py`` as shown below:

.. code-block:: python

   disabled_apps = ['publication_workflow']
   for app in disabled_apps:
       INSTALLED_APPS = filter(lambda a: a != app, INSTALLED_APPS)

When the publication workflow is enabled, you should see the "My Publications" link in the menu bar:

.. image:: _images/my-publications-link.png


Publication Workflow Settings
=============================
To use the default publication workflow settings, add the following to your ``tardis/settings.py``:

.. code-block:: python

  from tardis.apps.publication_workflow.default_settings import *


Installing Licenses
===================
The publication workflow app contains Creative Commons licenses in
``tardis/apps/publication_workflow/fixtures/licenses.json`` which
can be installed with:

.. code-block:: python

  python mytardis.py loaddata licenses

.. image:: _images/licenses.png

