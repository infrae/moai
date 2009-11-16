
from lxml.builder import ElementMaker

from moai import MetaDataFormat, name
from moai.metadata import OAIDC, MODS, XSI_NS

        
class DIDL(MetaDataFormat):
    """A metadata prefix implementing the DARE DIDL metadata format
    this format is registered under the name "didl"
    Note that this format re-uses oai_dc and mods formats that come with
    MOAI by default
    """
    
    name('didl')
    
    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'didl': "urn:mpeg:mpeg21:2002:02-DIDL-NS",
                   'dii': "urn:mpeg:mpeg21:2002:01-DII-NS",
                   'dip': "urn:mpeg:mpeg21:2005:01-DIP-NS",
                   'dcterms': "http://purl.org/dc/terms/",
                   'xsi': "http://www.w3.org/2001/XMLSchema-instance",
                   'dc': 'http://purl.org/dc/elements/1.1/',
                   }

        self.schemas = {'didl':'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/did/didl.xsd',
                        'dii': 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/dii/dii.xsd',
                        'dip': 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/dip/dip.xsd'}
        
    def __call__(self, element, metadata):
        data = metadata.record
        
        DIDL = ElementMaker(namespace=self.ns['didl'], nsmap=self.ns)
        DII = ElementMaker(namespace=self.ns['dii'])
        DIP = ElementMaker(namespace=self.ns['dip'])
        DCTERMS = ElementMaker(namespace=self.ns['dcterms'])

        oai_url = (self.config.url+'?verb=GetRecord&'
                   'metadataPrefix=%s&identifier=%s' % (
            self.prefix,
            self.config.get_oai_id(data['record']['id'])))

        # generate mods for this feed
        mods_data = DIDL.Resource(mimeType="application/xml")
        MODS('mods', self.config, self.db)(mods_data, metadata)

        asset_data = []
        
        didl = DIDL.DIDL(
            DIDL.Item(
             DIDL.Descriptor(
              DIDL.Statement(
               DCTERMS.modified(data['record']['when_modified'].isoformat().split('.')[0]),
               mimeType="application/xml"
               )
              ),
             DIDL.Component(
              DIDL.Resource(ref=oai_url,mimeType="application/xml")
              ),
             DIDL.Item(
              DIDL.Descriptor(
               DIDL.Statement(
                DIP.ObjectType('info:eu-repo/semantics/descriptiveMetadata'),
                mimeType="application/xml")
               ),
              DIDL.Component(mods_data)
              ),
             )
            )
        for root_item in didl:
            for asset_id in data['metadata'].get('asset', []):
                asset = self.db.get_metadata(asset_id)
                url = asset['url'][0]
                if not url.startswith('http://'):
                    url = self.config.url.rstrip('/') + '/' + url.lstrip('/')
                item = DIDL.Item(
                    DIDL.Descriptor(
                     DIDL.Statement(
                      DIP.ObjectType('info:eu-repo/semantics/objectFile'),
                      mimeType="application/xml")
                     ),
                    DIDL.Component(
                     DIDL.Resource(mimeType=asset['mimetype'][0],
                                   ref=url)
                     )
                    )
                root_item.append(item)
            break
        
        
        if data['metadata'].get('url'):
             item = DIDL.Item(
                 DIDL.Descriptor(
                  DIDL.Statement(
                   DIP.ObjectType('info:eu-repo/semantics/humanStartPage'),
                   mimeType="application/xml")
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
