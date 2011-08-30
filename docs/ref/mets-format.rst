.. _ref-mets-format:

================
METS File Format
================

This section introduces the METS file format and how it is used by MyTARDIS.

The Metadata Encoding & Transmission Standard (METS) is defined at http://www.loc.gov/standards/mets/.  A good overview is available from: http://www.loc.gov/standards/mets/presentations/METS.ppt.

The XML fragments below are all taken from this :doc:`mets-example`.

The METS file is broken up in to a number of sections:

<metsHrd>
---------

The metsHdr contains the institution name of the experiment, as shown below::

  <metsHdr CREATEDATE="2011-08-30T11:52:27" LASTMODDATE="2011-08-30T11:52:27">
    <agent ROLE="DISSEMINATOR" TYPE="ORGANIZATION">
      <name>Adelaide University</name>
    </agent>
    <agent ROLE="CREATOR" TYPE="OTHER">
      <name>METS Exporter 0.1</name>
    </agent>
  </metsHdr>

The key attributes / values are:

 * Organisation Name: Institution

<dmdSec>
--------

A Descriptive Metadata Section is created for the core experiment metadata and each dataset.

The experiment core metadata has an id of "E-1" and datasets have an id of "D-x", where x is a simple iterator, as shown below::

  <dmdSec ID="E-1">
    <mdWrap MDTYPE="MODS">
      <xmlData>
        <mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
          <mods:titleInfo>
            <mods:title>SAXS Test</mods:title>
          </mods:titleInfo>
          <mods:genre>experiment</mods:genre>
          <mods:relatedItem type="otherVersion">
            <mods:originInfo>
              <mods:publisher>Primary Citation</mods:publisher>
            </mods:originInfo>
            <mods:location>http://www.blahblah.com/espanol</mods:location>
          </mods:relatedItem>
          <mods:abstract>Hello world hello world</mods:abstract>
          <tardis:tardis xmlns:tardis="http://tardisdates.com/">
            <tardis:startTime>2011-12-31 13:55:00</tardis:startTime>
            <tardis:endTime>2035-11-29 14:33:00</tardis:endTime>
          </tardis:tardis>
          <mods:name type="personal">
            <mods:namePart>Gerry G.</mods:namePart>
            <mods:role>
              <mods:roleTerm type="text">author</mods:roleTerm>
            </mods:role>
          </mods:name>
          <mods:name type="personal">
            <mods:namePart>Alvin K</mods:namePart>
            <mods:role>
              <mods:roleTerm type="text">author</mods:roleTerm>
            </mods:role>
          </mods:name>
          <mods:name type="personal">
            <mods:namePart>Moscatto Brothers</mods:namePart>
            <mods:role>
              <mods:roleTerm type="text">author</mods:roleTerm>
            </mods:role>
          </mods:name>
        </mods:mods>
      </xmlData>
    </mdWrap>
  </dmdSec>
  <dmdSec ID="D-1">
    <mdWrap MDTYPE="MODS">
      <xmlData>
        <mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
          <mods:titleInfo>
            <mods:title>Bluebird</mods:title>
          </mods:titleInfo>
        </mods:mods>
      </xmlData>
    </mdWrap>
  </dmdSec>

The key attributes / values are:

Experiment:

 * mods:title: The Experiment Title
 * mods:abstract: The Experiment Abstract / Description
 * tardis:startTime: The Experiment Start Date
 * tardis:endTime: The Experiment End Date
 * mods:namePart: The Experiment Authors

Dataset:

 * mods:title: The Dataset Description



<amdSec>
--------

An Administrative Metadata Section is created for each parameter set.  Each parameter set is assigned an id of "A-x", where x is a simple iterator, as shown below::

  <amdSec>
    <techMD ID="A-1">
      <mdWrap MDTYPE="OTHER" OTHERMDTYPE="TARDISEXPERIMENT">
        <xmlData>
          <tardis:experiment xmlns:tardis="http://www.tardis.edu.au/schemas/as/experiment/2010/09/21">
            <tardis:EPN>1234</tardis:EPN>
            <tardis:beamline>METS Test</tardis:beamline>
          </tardis:experiment>
        </xmlData>
      </mdWrap>
    </techMD>
    <techMD ID="A-2">
      <mdWrap MDTYPE="OTHER" OTHERMDTYPE="TARDISDATASET">
        <xmlData>
          <tardis:dataset xmlns:tardis="http://www.tardis.edu.au/schemas/saxs/dataset/2010/08/10">
            <tardis:frqimn>0.0450647</tardis:frqimn>
            <tardis:frxcen>411.947</tardis:frxcen>
            <tardis:frleng>554.619</tardis:frleng>
            <tardis:frwlen>0.6702</tardis:frwlen>
            <tardis:frqimx>2.26206</tardis:frqimx>
            <tardis:frtype>PIL200K</tardis:frtype>
            <tardis:frycen>559.038</tardis:frycen>
          </tardis:dataset>
        </xmlData>
      </mdWrap>
    </techMD>
    <techMD ID="A-3">
      <mdWrap MDTYPE="OTHER" OTHERMDTYPE="TARDISDATAFILE">
        <xmlData>
          <tardis:datafile xmlns:tardis="http://www.tardis.edu.au/schemas/saxs/datafile/2010/08/10">
            <tardis:positionerString>UDEF1_2_PV1_2_3_4_5</tardis:positionerString>
            <tardis:countingSecs>10.0</tardis:countingSecs>
            <tardis:ibsBgnd>0.0</tardis:ibsBgnd>
            <tardis:it>290.0</tardis:it>
            <tardis:positionerValues>49.4420 1.2914 20.000 12.000 26.316 2.0007 1.2999</tardis:positionerValues>
            <tardis:itBgnd>0.0</tardis:itBgnd>
            <tardis:io>281443.0</tardis:io>
            <tardis:ioBgnd>0.0</tardis:ioBgnd>
            <tardis:timeStampString>Fri Apr 16 03:15:16 2010</tardis:timeStampString>
            <tardis:ibs>679274.0</tardis:ibs>
          </tardis:datafile>
        </xmlData>
      </mdWrap>
    </techMD>
    ...
  </amdSec>

The key attributes / values are:

 * xmlns:tardis: The namespace of the schema
 * tardis:<parameter name>: Each parameter in the parameter set.


<fileSec>
---------

MyTARDIS creates a single File Group within the File Section, and a File entry for each datafile.  The ADMID attribute links in the Parameter Sets defined in the amdSec, as shown below::

  <fileSec>
    <fileGrp USE="original">
      <file ADMID="A-3" CHECKSUM="application/octet-stream" CHECKSUMTYPE="MD5" ID="F-1" MIMETYPE="application/octet-stream" OWNERID="ment0001.osc" SIZE="18006000">
        <FLocat LOCTYPE="URL" xlink:href="tardis://Images/ment0001.osc" xlink:type="simple"/>
      </file>
      ...
    </fileGrp>
  </fileSec>

The key attributes / values are:

 * MIMETYPE: The file mime-type
 * OWNERID: The file name
 * SIZE: The file size in bytes
 * xlink:href: The url of the file



<structMap>
-----------

The Structure Map is used to group datafiles in to datasets, as shown below::

  <structMap TYPE="logical">
    <div ADMID="A-1" DMDID="E-1" TYPE="investigation">
      <div ADMID="A-2" DMDID="D-1" TYPE="dataset">
        <fptr FILEID="F-1"/>
        <fptr FILEID="F-2"/>
        <fptr FILEID="F-3"/>
        <fptr FILEID="F-4"/>
        <fptr FILEID="F-5"/>
      </div>
    </div>
  </structMap>


<structLink>
------------

Unused by MyTARDIS.

<behaviorSec>
-------------

Unused by MyTARDIS.

