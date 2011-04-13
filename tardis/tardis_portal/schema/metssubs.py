#
# Generated Thu Mar 17 13:49:32 2011 by generateDS.py version 2.4b.
#

import sys

import tardis.tardis_portal.schema.mets as supermod

etree_ = None
Verbose_import_ = False
(XMLParser_import_none, XMLParser_import_lxml,
 XMLParser_import_elementtree
 ) = range(3)
XMLParser_import_library = None
try:
    # lxml
    from lxml import etree as etree_
    XMLParser_import_library = XMLParser_import_lxml
    if Verbose_import_:
        print("running with lxml.etree")
except ImportError:
    try:
        # cElementTree from Python 2.5+
        import xml.etree.cElementTree as etree_
        XMLParser_import_library = XMLParser_import_elementtree
        if Verbose_import_:
            print("running with cElementTree on Python 2.5+")
    except ImportError:
        try:
            # ElementTree from Python 2.5+
            import xml.etree.ElementTree as etree_
            XMLParser_import_library = XMLParser_import_elementtree
            if Verbose_import_:
                print("running with ElementTree on Python 2.5+")
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree_
                XMLParser_import_library = XMLParser_import_elementtree
                if Verbose_import_:
                    print("running with cElementTree")
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree_
                    XMLParser_import_library = XMLParser_import_elementtree
                    if Verbose_import_:
                        print("running with ElementTree")
                except ImportError:
                    raise ImportError("Failed to import ElementTree from any known place")


def parsexml_(*args, **kwargs):
    if (XMLParser_import_library == XMLParser_import_lxml and
        'parser' not in kwargs):
        # Use the lxml ElementTree compatible parser so that, e.g.,
        #   we ignore comments.
        kwargs['parser'] = etree_.ETCompatXMLParser()
    doc = etree_.parse(*args, **kwargs)
    return doc

#
# Globals
#

ExternalEncoding = 'ascii'

#
# Data representation classes
#


class metsTypeSub(supermod.metsType):
    def __init__(self, PROFILE=None, LABEL=None, TYPE=None, ID=None, OBJID=None, metsHdr=None, dmdSec=None, amdSec=None, fileSec=None, structMap=None, structLink=None, behaviorSec=None):
        super(metsTypeSub, self).__init__(PROFILE, LABEL, TYPE, ID, OBJID, metsHdr, dmdSec, amdSec, fileSec, structMap, structLink, behaviorSec, )
supermod.metsType.subclass = metsTypeSub
# end class metsTypeSub


class metsHdrSub(supermod.metsHdr):
    def __init__(self, CREATEDATE=None, RECORDSTATUS=None, ADMID=None, LASTMODDATE=None, ID=None, agent=None, altRecordID=None, metsDocumentID=None):
        super(metsHdrSub, self).__init__(CREATEDATE, RECORDSTATUS, ADMID, LASTMODDATE, ID, agent, altRecordID, metsDocumentID, )
supermod.metsHdr.subclass = metsHdrSub
# end class metsHdrSub


class agentSub(supermod.agent):
    def __init__(self, TYPE=None, OTHERTYPE=None, ROLE=None, ID=None, OTHERROLE=None, name=None, note=None):
        super(agentSub, self).__init__(TYPE, OTHERTYPE, ROLE, ID, OTHERROLE, name, note, )
supermod.agent.subclass = agentSub
# end class agentSub


class altRecordIDSub(supermod.altRecordID):
    def __init__(self, TYPE=None, ID=None, valueOf_=None):
        super(altRecordIDSub, self).__init__(TYPE, ID, valueOf_, )
supermod.altRecordID.subclass = altRecordIDSub
# end class altRecordIDSub


class metsDocumentIDSub(supermod.metsDocumentID):
    def __init__(self, TYPE=None, ID=None, valueOf_=None):
        super(metsDocumentIDSub, self).__init__(TYPE, ID, valueOf_, )
supermod.metsDocumentID.subclass = metsDocumentIDSub
# end class metsDocumentIDSub


class fileSecSub(supermod.fileSec):
    def __init__(self, ID=None, fileGrp=None):
        super(fileSecSub, self).__init__(ID, fileGrp, )
supermod.fileSec.subclass = fileSecSub
# end class fileSecSub


class amdSecTypeSub(supermod.amdSecType):
    def __init__(self, ID=None, techMD=None, rightsMD=None, sourceMD=None, digiprovMD=None):
        super(amdSecTypeSub, self).__init__(ID, techMD, rightsMD, sourceMD, digiprovMD, )
supermod.amdSecType.subclass = amdSecTypeSub
# end class amdSecTypeSub


class fileGrpTypeSub(supermod.fileGrpType):
    def __init__(self, VERSDATE=None, ADMID=None, ID=None, USE=None, fileGrp=None, file=None):
        super(fileGrpTypeSub, self).__init__(VERSDATE, ADMID, ID, USE, fileGrp, file, )
supermod.fileGrpType.subclass = fileGrpTypeSub
# end class fileGrpTypeSub


class structMapTypeSub(supermod.structMapType):
    def __init__(self, TYPE=None, ID=None, LABEL=None, div=None):
        super(structMapTypeSub, self).__init__(TYPE, ID, LABEL, div, )
supermod.structMapType.subclass = structMapTypeSub
# end class structMapTypeSub


class divTypeSub(supermod.divType):
    def __init__(self, ADMID=None, TYPE=None, LABEL=None, DMDID=None, ORDERLABEL=None, CONTENTIDS=None, label=None, ORDER=None, ID=None, mptr=None, fptr=None, div=None):
        super(divTypeSub, self).__init__(ADMID, TYPE, LABEL, DMDID, ORDERLABEL, CONTENTIDS, label, ORDER, ID, mptr, fptr, div, )
supermod.divType.subclass = divTypeSub
# end class divTypeSub


class mptrSub(supermod.mptr):
    def __init__(self, arcrole=None, show=None, OTHERLOCTYPE=None, title=None, actuate=None, href=None, role=None, LOCTYPE=None, CONTENTIDS=None, type_=None, ID=None, valueOf_=None):
        super(mptrSub, self).__init__(arcrole, show, OTHERLOCTYPE, title, actuate, href, role, LOCTYPE, CONTENTIDS, type_, ID, valueOf_, )
supermod.mptr.subclass = mptrSub
# end class mptrSub


class fptrSub(supermod.fptr):
    def __init__(self, CONTENTIDS=None, ID=None, FILEID=None, par=None, seq=None, area=None):
        super(fptrSub, self).__init__(CONTENTIDS, ID, FILEID, par, seq, area, )
supermod.fptr.subclass = fptrSub
# end class fptrSub


class parTypeSub(supermod.parType):
    def __init__(self, ID=None, area=None, seq=None):
        super(parTypeSub, self).__init__(ID, area, seq, )
supermod.parType.subclass = parTypeSub
# end class parTypeSub


class seqTypeSub(supermod.seqType):
    def __init__(self, ID=None, area=None, par=None):
        super(seqTypeSub, self).__init__(ID, area, par, )
supermod.seqType.subclass = seqTypeSub
# end class seqTypeSub


class areaTypeSub(supermod.areaType):
    def __init__(self, BEGIN=None, END=None, BETYPE=None, SHAPE=None, COORDS=None, EXTENT=None, CONTENTIDS=None, ADMID=None, ID=None, EXTTYPE=None, FILEID=None, valueOf_=None):
        super(areaTypeSub, self).__init__(BEGIN, END, BETYPE, SHAPE, COORDS, EXTENT, CONTENTIDS, ADMID, ID, EXTTYPE, FILEID, valueOf_, )
supermod.areaType.subclass = areaTypeSub
# end class areaTypeSub


class structLinkTypeSub(supermod.structLinkType):
    def __init__(self, ID=None, smLink=None, smLinkGrp=None):
        super(structLinkTypeSub, self).__init__(ID, smLink, smLinkGrp, )
supermod.structLinkType.subclass = structLinkTypeSub
# end class structLinkTypeSub


class smLinkSub(supermod.smLink):
    def __init__(self, fromxx=None, show=None, title=None, actuate=None, to=None, arcrole=None, ID=None, valueOf_=None):
        super(smLinkSub, self).__init__(fromxx, show, title, actuate, to, arcrole, ID, valueOf_, )
supermod.smLink.subclass = smLinkSub
# end class smLinkSub


class smLinkGrpSub(supermod.smLinkGrp):
    def __init__(self, role=None, title=None, ARCLINKORDER='unordered', ID=None, type_=None, smLocatorLink=None, smArcLink=None):
        super(smLinkGrpSub, self).__init__(role, title, ARCLINKORDER, ID, type_, smLocatorLink, smArcLink, )
supermod.smLinkGrp.subclass = smLinkGrpSub
# end class smLinkGrpSub


class smLocatorLinkSub(supermod.smLocatorLink):
    def __init__(self, title=None, label=None, href=None, role=None, type_=None, ID=None, valueOf_=None):
        super(smLocatorLinkSub, self).__init__(title, label, href, role, type_, ID, valueOf_, )
supermod.smLocatorLink.subclass = smLocatorLinkSub
# end class smLocatorLinkSub


class smArcLinkSub(supermod.smArcLink):
    def __init__(self, ADMID=None, fromxx=None, title=None, show=None, actuate=None, ARCTYPE=None, to=None, arcrole=None, type_=None, ID=None, valueOf_=None):
        super(smArcLinkSub, self).__init__(ADMID, fromxx, title, show, actuate, ARCTYPE, to, arcrole, type_, ID, valueOf_, )
supermod.smArcLink.subclass = smArcLinkSub
# end class smArcLinkSub


class behaviorSecTypeSub(supermod.behaviorSecType):
    def __init__(self, LABEL=None, ID=None, CREATED=None, behaviorSec=None, behavior=None):
        super(behaviorSecTypeSub, self).__init__(LABEL, ID, CREATED, behaviorSec, behavior, )
supermod.behaviorSecType.subclass = behaviorSecTypeSub
# end class behaviorSecTypeSub


class behaviorTypeSub(supermod.behaviorType):
    def __init__(self, ADMID=None, CREATED=None, STRUCTID=None, LABEL=None, GROUPID=None, BTYPE=None, ID=None, interfaceDef=None, mechanism=None):
        super(behaviorTypeSub, self).__init__(ADMID, CREATED, STRUCTID, LABEL, GROUPID, BTYPE, ID, interfaceDef, mechanism, )
supermod.behaviorType.subclass = behaviorTypeSub
# end class behaviorTypeSub


class objectTypeSub(supermod.objectType):
    def __init__(self, arcrole=None, title=None, OTHERLOCTYPE=None, show=None, actuate=None, LABEL=None, href=None, role=None, LOCTYPE=None, type_=None, ID=None, valueOf_=None):
        super(objectTypeSub, self).__init__(arcrole, title, OTHERLOCTYPE, show, actuate, LABEL, href, role, LOCTYPE, type_, ID, valueOf_, )
supermod.objectType.subclass = objectTypeSub
# end class objectTypeSub


class mdSecTypeSub(supermod.mdSecType):
    def __init__(self, STATUS=None, ADMID=None, CREATED=None, ID=None, GROUPID=None, mdRef=None, mdWrap=None):
        super(mdSecTypeSub, self).__init__(STATUS, ADMID, CREATED, ID, GROUPID, mdRef, mdWrap, )
supermod.mdSecType.subclass = mdSecTypeSub
# end class mdSecTypeSub


class mdRefSub(supermod.mdRef):
    def __init__(self, MIMETYPE=None, arcrole=None, XPTR=None, CHECKSUMTYPE=None, show=None, OTHERLOCTYPE=None, CHECKSUM=None, OTHERMDTYPE=None, title=None, actuate=None, MDTYPE=None, LABEL=None, href=None, role=None, LOCTYPE=None, MDTYPEVERSION=None, CREATED=None, type_=None, ID=None, SIZE=None, valueOf_=None):
        super(mdRefSub, self).__init__(MIMETYPE, arcrole, XPTR, CHECKSUMTYPE, show, OTHERLOCTYPE, CHECKSUM, OTHERMDTYPE, title, actuate, MDTYPE, LABEL, href, role, LOCTYPE, MDTYPEVERSION, CREATED, type_, ID, SIZE, valueOf_, )
supermod.mdRef.subclass = mdRefSub
# end class mdRefSub


class mdWrapSub(supermod.mdWrap):
    def __init__(self, MIMETYPE=None, CHECKSUMTYPE=None, CREATED=None, CHECKSUM=None, OTHERMDTYPE=None, MDTYPE=None, LABEL=None, MDTYPEVERSION=None, ID=None, SIZE=None, binData=None, xmlData=None):
        super(mdWrapSub, self).__init__(MIMETYPE, CHECKSUMTYPE, CREATED, CHECKSUM, OTHERMDTYPE, MDTYPE, LABEL, MDTYPEVERSION, ID, SIZE, binData, xmlData, )
supermod.mdWrap.subclass = mdWrapSub
# end class mdWrapSub


class fileTypeSub(supermod.fileType):
    def __init__(self, MIMETYPE=None, ADMID=None, END=None, CHECKSUMTYPE=None, SEQ=None, CREATED=None, CHECKSUM=None, USE=None, ID=None, DMDID=None, BEGIN=None, OWNERID=None, SIZE=None, GROUPID=None, BETYPE=None, FLocat=None, FContent=None, stream=None, transformFile=None, file=None):
        super(fileTypeSub, self).__init__(MIMETYPE, ADMID, END, CHECKSUMTYPE, SEQ, CREATED, CHECKSUM, USE, ID, DMDID, BEGIN, OWNERID, SIZE, GROUPID, BETYPE, FLocat, FContent, stream, transformFile, file, )
supermod.fileType.subclass = fileTypeSub
# end class fileTypeSub


class FLocatSub(supermod.FLocat):
    def __init__(self, arcrole=None, USE=None, title=None, OTHERLOCTYPE=None, show=None, actuate=None, href=None, role=None, LOCTYPE=None, type_=None, ID=None, valueOf_=None):
        super(FLocatSub, self).__init__(arcrole, USE, title, OTHERLOCTYPE, show, actuate, href, role, LOCTYPE, type_, ID, valueOf_, )
supermod.FLocat.subclass = FLocatSub
# end class FLocatSub


class FContentSub(supermod.FContent):
    def __init__(self, USE=None, ID=None, binData=None, xmlData=None):
        super(FContentSub, self).__init__(USE, ID, binData, xmlData, )
supermod.FContent.subclass = FContentSub
# end class FContentSub


class streamSub(supermod.stream):
    def __init__(self, BEGIN=None, END=None, ADMID=None, BETYPE=None, streamType=None, DMDID=None, OWNERID=None, ID=None, valueOf_=None):
        super(streamSub, self).__init__(BEGIN, END, ADMID, BETYPE, streamType, DMDID, OWNERID, ID, valueOf_, )
supermod.stream.subclass = streamSub
# end class streamSub


class transformFileSub(supermod.transformFile):
    def __init__(self, TRANSFORMTYPE=None, TRANSFORMKEY=None, TRANSFORMBEHAVIOR=None, TRANSFORMALGORITHM=None, TRANSFORMORDER=None, ID=None, valueOf_=None):
        super(transformFileSub, self).__init__(TRANSFORMTYPE, TRANSFORMKEY, TRANSFORMBEHAVIOR, TRANSFORMALGORITHM, TRANSFORMORDER, ID, valueOf_, )
supermod.transformFile.subclass = transformFileSub
# end class transformFileSub


class structLinkSub(supermod.structLink):
    def __init__(self, ID=None, smLink=None, smLinkGrp=None):
        super(structLinkSub, self).__init__(ID, smLink, smLinkGrp, )
supermod.structLink.subclass = structLinkSub
# end class structLinkSub


class fileGrpSub(supermod.fileGrp):
    def __init__(self, VERSDATE=None, ADMID=None, ID=None, USE=None, fileGrp=None, file=None):
        super(fileGrpSub, self).__init__(VERSDATE, ADMID, ID, USE, fileGrp, file, )
supermod.fileGrp.subclass = fileGrpSub
# end class fileGrpSub


class metsSub(supermod.mets):
    def __init__(self, PROFILE=None, LABEL=None, TYPE=None, ID=None, OBJID=None, metsHdr=None, dmdSec=None, amdSec=None, fileSec=None, structMap=None, structLink=None, behaviorSec=None):
        super(metsSub, self).__init__(PROFILE, LABEL, TYPE, ID, OBJID, metsHdr, dmdSec, amdSec, fileSec, structMap, structLink, behaviorSec, )
supermod.mets.subclass = metsSub
# end class metsSub


def get_root_tag(node):
    tag = supermod.Tag_pattern_.match(node.tag).groups()[-1]
    rootClass = None
    if hasattr(supermod, tag):
        rootClass = getattr(supermod, tag)
    return tag, rootClass


def parse(inFilename):
    doc = parsexml_(inFilename)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'mets'
        rootClass = supermod.mets
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\n')
    rootObj.export(sys.stdout, 0, name_=rootTag,
        namespacedef_='')
    doc = None
    return rootObj


def parseString(inString):
    from StringIO import StringIO
    doc = parsexml_(StringIO(inString))
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'mets'
        rootClass = supermod.mets
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\n')
    rootObj.export(sys.stdout, 0, name_=rootTag,
        namespacedef_='')
    return rootObj


def parseLiteral(inFilename):
    doc = parsexml_(inFilename)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'mets'
        rootClass = supermod.mets
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('#from ??? import *\n\n')
    sys.stdout.write('import ??? as model_\n\n')
    sys.stdout.write('rootObj = model_.mets(\n')
    rootObj.exportLiteral(sys.stdout, 0, name_="mets")
    sys.stdout.write(')\n')
    return rootObj


USAGE_TEXT = """
Usage: python ???.py <infilename>
"""


def usage():
    print USAGE_TEXT
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        usage()
    infilename = args[0]
    root = parse(infilename)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()
