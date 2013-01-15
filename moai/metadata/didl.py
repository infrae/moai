
from lxml.builder import ElementMaker

from moai.metadata.mods import NL_MODS, XSI_NS

        
class DIDL(object):
    """A metadata prefix implementing the DARE DIDL metadata format
    this format is registered under the name "didl"
    Note that this format re-uses oai_dc and mods formats that come with
    MOAI by default
    """
        
    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'didl': "urn:mpeg:mpeg21:2002:02-DIDL-NS",
                   'dii': "urn:mpeg:mpeg21:2002:01-DII-NS",
                   'dip': "urn:mpeg:mpeg21:2005:01-DIP-NS",
                   'dcterms': "http://purl.org/dc/terms/",
                   'xsi': "http://www.w3.org/2001/XMLSchema-instance",
                   'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                   'dc': 'http://purl.org/dc/elements/1.1/',
                   }

        self.schemas = {'didl':'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/did/didl.xsd',
                        'dii': 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/dii/dii.xsd',
                        'dip': 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/dip/dip.xsd'}
        
    def get_namespace(self):
        return self.ns[self.prefix]

    def get_schema_location(self):
        return self.schemas[self.prefix]

        
    def __call__(self, element, metadata):
        data = metadata.record
        
        DIDL = ElementMaker(namespace=self.ns['didl'], nsmap=self.ns)
        DII = ElementMaker(namespace=self.ns['dii'])
        DIP = ElementMaker(namespace=self.ns['dip'])
        RDF = ElementMaker(namespace=self.ns['rdf'])
        DCTERMS = ElementMaker(namespace=self.ns['dcterms'])

        oai_url = (self.config.url+'?verb=GetRecord&'
                   'metadataPrefix=%s&identifier=%s' % (
            self.prefix,
            data['id']))

        id_url = data['metadata'].get('url', [None])[0]        

        # generate mods for this feed
        mods_data = DIDL.Resource(mimeType="application/xml")
        NL_MODS('mods', self.config, self.db)(mods_data, metadata)

        asset_data = []

        descriptive_metadata = RDF.type()
        descriptive_metadata.attrib['{%s}resource' % self.ns['rdf']] = (
            'info:eu-repo/semantics/descriptiveMetadata')
        
        didl = DIDL.DIDL(
            DIDL.Item(
             DIDL.Descriptor(
              DIDL.Statement(
               DCTERMS.modified(data['modified'].isoformat().split('.')[0]),
               mimeType="application/xml"
               )
              ),
             DIDL.Component(
              DIDL.Resource(ref=id_url or oai_url,mimeType="application/xml")
              ),
             DIDL.Item(
              DIDL.Descriptor(
               DIDL.Statement(descriptive_metadata, mimeType="application/xml")
               ),
              DIDL.Component(
                DIDL.Descriptor(
                   DIDL.Statement("mods", mimeType="text/plain")),
                mods_data)
              ),
             )
            )

        object_file = RDF.type()
        object_file.attrib['{%s}resource' % self.ns['rdf']] = (
            'info:eu-repo/semantics/objectFile')
        for root_item in didl:
            for asset in data['metadata'].get('asset', []):
                url = asset['url']
                if not url.startswith('http://'):
                    url = self.config.url.rstrip('/') + '/' + url.lstrip('/')
                item = DIDL.Item(
                    DIDL.Descriptor(
                     DIDL.Statement(object_file, mimeType="application/xml")
                     )
                    )
                access = asset.get('access')
                if access == 'open':
                    access = (
                        'http://purl.org/eprint/accessRights/OpenAccess')
                elif access == 'restricted':
                    access = (
                        'http://purl.org/eprint/accessRights/RestrictedAccess')
                elif access == 'closed':
                    access = (
                        'http://purl.org/eprint/accessRights/ClosedAccess')
                if access:
                    item.append(
                        DIDL.Descriptor(
                        DIDL.Statement(DCTERMS.accessRights(access),
                                       mimeType="application/xml")))
                for modified in asset.get('modified', []):
                    item.append(
                        DIDL.Descriptor(
                                DIDL.Statement(DCTERMS.modified(modified),
                                               mimeType="application/xml")))
                    
                item.append(
                    DIDL.Component(
                     DIDL.Resource(mimeType=asset['mimetype'],
                                   ref=url)
                     )
                    )

                root_item.append(item)
            break
        
        human_start_page = RDF.type()
        human_start_page.attrib['{%s}resource' % self.ns['rdf']] = (
            'info:eu-repo/semantics/humanStartPage')
        if data['metadata'].get('url'):
             item = DIDL.Item(
                 DIDL.Descriptor(
                  DIDL.Statement(human_start_page, mimeType="application/xml")
                  ),
                 DIDL.Component(
                  DIDL.Resource(mimeType="text/html", ref=data['metadata']['url'][0])
                 )
                )
             root_item.append(item)
        
        didl.attrib['{%s}schemaLocation' % XSI_NS] = (
            '%s %s %s %s %s %s' % (self.ns['didl'],
                                   self.schemas['didl'],
                                   self.ns['dii'],
                                   self.schemas['dii'],
                                   self.ns['dip'],
                                   self.schemas['dip']))
        element.append(didl)
