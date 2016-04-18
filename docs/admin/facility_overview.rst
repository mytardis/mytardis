Facility Overview
=================

Introduction
------------

The Facility Overview included with MyTardis allows facility administrators
to monitor the output of connected instruments, highlighting unverified
files, dataset size, file counts and file listings.

Setup
-----
In order for datasets to appear in the Facility Overview, each dataset must
be associated with an Instrument, which is itself associated with a Facility.
The Facility object will reference a facility administrator's group, members of
which may view the Facility Overview.

::

     +-------------------+   +------------------------+   +----------+
     | Facility Managers |-->| Facility Manager Group |-->| Facility |
     +-------------------+   +------------------------+   +----------+
  |------------------------------------------------------------|
  |
  |  +------------+   +----------+   +-----------+
  |->| Instrument |-->| Datasets |-->| Datafiles |
     +------------+   +----------+   +-----------+
                            ^
                            |  +-------------+
                            |--| Experiments |
                               +-------------+

The facility managers, facility manager groups, facilities and instruments
may be configured via the django admin interface. MyData, the desktop
uploader client for the MyTardis server, can be configured to assign the
appropriate instrument to uploaded datasets at the point of ingestion.

It should be noted that the dataset visibility within the facility overview
is limited to dataset and datafile listings only. Access to the experiment and
dataset views, as well as raw data, is still controlled via the
:doc:`ACL framework<../dev/authorisation>`.

Usage
-----

Members of the facility manager groups for one or more facilities will see
the "Facility Overview" menu item in the MyTardis web portal. After opening
the facility overview, a list of recently ingested datasets will be
displayed from the facility being managed. If a user manages multiple
facilities, a blue drop-down selector will also appear on the right-hand side
of the page. As the facility overview is designed to give a snapshot of
recently uploaded datasets, older data is not immediately accessible;
MyTardis' :doc:`search feature<searchsetup>` is better suited to this.

In addition to simply listing the most recent datasets, the datasets can be
grouped by instrument or by owner, and filtered by username, experiment name
and instrument name. Note that while filters are active, it may appear as
though no new pages are loaded by clicking "Load more", since the additional
datasets fetched from the server might not match the active filters.