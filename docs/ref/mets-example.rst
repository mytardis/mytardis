.. _ref-mets-example:

============
METS Example
============

The METS file included below is the example from :doc:`ref/mets-format`::
  
  <?xml version="1.0" ?>
  <mets LABEL="" OBJID="A-1" PROFILE="Scientific Dataset Profile 1.0" TYPE="study" xmlns="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd" xsi:type="mets">
    <metsHdr CREATEDATE="2011-08-30T11:52:27" LASTMODDATE="2011-08-30T11:52:27">
      <agent ROLE="DISSEMINATOR" TYPE="ORGANIZATION">
        <name>Adelaide University</name>
      </agent>
      <agent ROLE="CREATOR" TYPE="OTHER">
        <name>METS Exporter 0.1</name>
      </agent>
    </metsHdr>
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
      <techMD ID="A-4">
        <mdWrap MDTYPE="OTHER" OTHERMDTYPE="TARDISDATAFILE">
          <xmlData>
            <tardis:datafile xmlns:tardis="http://www.tardis.edu.au/schemas/saxs/datafile/2010/08/10">
              <tardis:positionerString>UDEF1_2_PV1_2_3_4_5</tardis:positionerString>
              <tardis:countingSecs>10.0</tardis:countingSecs>
              <tardis:ibsBgnd>0.0</tardis:ibsBgnd>
              <tardis:it>284.0</tardis:it>
              <tardis:positionerValues>2.7070 -0.7136 20.000 12.000 26.319 2.0007 1.2999</tardis:positionerValues>
              <tardis:itBgnd>0.0</tardis:itBgnd>
              <tardis:io>312003.0</tardis:io>
              <tardis:ioBgnd>0.0</tardis:ioBgnd>
              <tardis:timeStampString>Fri Apr 16 01:21:15 2010</tardis:timeStampString>
              <tardis:ibs>750369.0</tardis:ibs>
            </tardis:datafile>
          </xmlData>
        </mdWrap>
      </techMD>
      <techMD ID="A-5">
        <mdWrap MDTYPE="OTHER" OTHERMDTYPE="TARDISDATAFILE">
          <xmlData>
            <tardis:datafile xmlns:tardis="http://www.tardis.edu.au/schemas/saxs/datafile/2010/08/10">
              <tardis:positionerString>UDEF1_2_PV1_2_3_4_5</tardis:positionerString>
              <tardis:countingSecs>10.0</tardis:countingSecs>
              <tardis:ibsBgnd>0.0</tardis:ibsBgnd>
              <tardis:it>288.0</tardis:it>
              <tardis:positionerValues>0.2460 25.6814 20.000 12.000 26.325 2.0007 1.2999</tardis:positionerValues>
              <tardis:itBgnd>0.0</tardis:itBgnd>
              <tardis:io>277803.0</tardis:io>
              <tardis:ioBgnd>0.0</tardis:ioBgnd>
              <tardis:timeStampString>Fri Apr 16 03:36:10 2010</tardis:timeStampString>
              <tardis:ibs>673307.0</tardis:ibs>
            </tardis:datafile>
          </xmlData>
        </mdWrap>
      </techMD>
      <techMD ID="A-6">
        <mdWrap MDTYPE="OTHER" OTHERMDTYPE="TARDISDATAFILE">
          <xmlData>
            <tardis:datafile xmlns:tardis="http://www.tardis.edu.au/schemas/saxs/datafile/2010/08/10">
              <tardis:positionerString>UDEF1_2_PV1_2_3_4_5</tardis:positionerString>
              <tardis:countingSecs>10.0</tardis:countingSecs>
              <tardis:ibsBgnd>0.0</tardis:ibsBgnd>
              <tardis:it>284.0</tardis:it>
              <tardis:positionerValues>24.7410 24.9764 20.000 12.000 26.322 2.0007 1.2999</tardis:positionerValues>
              <tardis:itBgnd>0.0</tardis:itBgnd>
              <tardis:io>274389.0</tardis:io>
              <tardis:ioBgnd>0.0</tardis:ioBgnd>
              <tardis:timeStampString>Fri Apr 16 03:53:30 2010</tardis:timeStampString>
              <tardis:ibs>665765.0</tardis:ibs>
            </tardis:datafile>
          </xmlData>
        </mdWrap>
      </techMD>
      <techMD ID="A-7">
        <mdWrap MDTYPE="OTHER" OTHERMDTYPE="TARDISDATAFILE">
          <xmlData>
            <tardis:datafile xmlns:tardis="http://www.tardis.edu.au/schemas/saxs/datafile/2010/08/10">
              <tardis:positionerString>UDEF1_2_PV1_2_3_4_5</tardis:positionerString>
              <tardis:countingSecs>10.0</tardis:countingSecs>
              <tardis:ibsBgnd>0.0</tardis:ibsBgnd>
              <tardis:it>284.0</tardis:it>
              <tardis:positionerValues>25.1410 25.3764 20.000 12.000 26.330 2.0007 1.2999</tardis:positionerValues>
              <tardis:itBgnd>0.0</tardis:itBgnd>
              <tardis:io>274321.0</tardis:io>
              <tardis:ioBgnd>0.0</tardis:ioBgnd>
              <tardis:timeStampString>Fri Apr 16 03:55:30 2010</tardis:timeStampString>
              <tardis:ibs>655498.0</tardis:ibs>
            </tardis:datafile>
          </xmlData>
        </mdWrap>
      </techMD>
    </amdSec>
    <fileSec>
      <fileGrp USE="original">
        <file ADMID="A-3" CHECKSUM="application/octet-stream" CHECKSUMTYPE="MD5" ID="F-1" MIMETYPE="application/octet-stream" OWNERID="ment0001.osc" SIZE="18006000">
          <FLocat LOCTYPE="URL" xlink:href="tardis://Images/ment0001.osc" xlink:type="simple"/>
        </file>
        <file ADMID="A-4" CHECKSUM="application/octet-stream" CHECKSUMTYPE="MD5" ID="F-2" MIMETYPE="application/octet-stream" OWNERID="ment0002.osc" SIZE="18006000">
          <FLocat LOCTYPE="URL" xlink:href="tardis://Images/ment0002.osc" xlink:type="simple"/>
        </file>
        <file ADMID="A-5" CHECKSUM="application/octet-stream" CHECKSUMTYPE="MD5" ID="F-3" MIMETYPE="application/octet-stream" OWNERID="ment0003.osc" SIZE="18006000">
          <FLocat LOCTYPE="URL" xlink:href="tardis://Images/ment0003.osc" xlink:type="simple"/>
        </file>
        <file ADMID="A-6" CHECKSUM="application/octet-stream" CHECKSUMTYPE="MD5" ID="F-4" MIMETYPE="application/octet-stream" OWNERID="ment0004.osc" SIZE="18006000">
          <FLocat LOCTYPE="URL" xlink:href="tardis://Images/ment0004.osc" xlink:type="simple"/>
        </file>
        <file ADMID="A-7" CHECKSUM="application/octet-stream" CHECKSUMTYPE="MD5" ID="F-5" MIMETYPE="application/octet-stream" OWNERID="ment0005.osc" SIZE="18006000">
          <FLocat LOCTYPE="URL" xlink:href="tardis://Images/ment0005.osc" xlink:type="simple"/>
        </file>
      </fileGrp>
    </fileSec>
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
  </mets>

