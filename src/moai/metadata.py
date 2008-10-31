
from lxml import etree
from lxml.builder import ElementMaker
from lxml.etree import SubElement

from moai import MataDataPrefix, name
from moai.meta import METADATA_PREFIXES

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

def get_writer(prefix, config, db):
    writer = METADATA_PREFIXES[prefix]
    return writer(prefix, config, db)


class OAIDC(MataDataPrefix):
    
    name('oai_dc')
    
    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                   'dc':'http://purl.org/dc/elements/1.1/'}
        self.schemas = {'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd'}
        
    def __call__(self, element, metadata):

        data = metadata.record
        
        OAI_DC =  ElementMaker(namespace=self.ns['oai_dc'],
                               nsmap =self.ns)
        DC = ElementMaker(namespace=self.ns['dc'])

        oai_dc = OAI_DC.dc()
        oai_dc.attrib['{%s}schemaLocation' % XSI_NS] = self.schemas['oai_dc']

        for field in ['title', 'creator', 'subject', 'description', 'publisher',
                      'contributor', 'type', 'format', 'identifier',
                      'source', 'language', 'relation', 'coverage', 'rights']:
            el = getattr(DC, field)
            for value in data['metadata'].get(field, []):
                oai_dc.append(el(value))

        for value in data['metadata'].get('date', []):
            oai_dc.append(DC.date(value.isoformat()))
        
        element.append(oai_dc)

class MODS(MataDataPrefix):
    
    name('mods')
    
    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'mods': 'http://www.loc.gov/mods/v3',
                   'xml':'http://www.w3.org/XML/1998/namespace',
                   'dai': 'info:eu-repo/dai'}

        self.schemas = {
           'mods': 'http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-2.xsd'}
        
    def __call__(self, element, metadata):

        data = metadata.record
        MODS = ElementMaker(namespace=self.ns['mods'], nsmap=self.ns)
        DAI = ElementMaker(namespace=self.ns['dai'], nsmap=self.ns)
        mods = MODS.mods(version="3.2")

        author_data = []
        for id in data['metadata'].get('author_rel', []):
            author = self.db.get_metadata(id)
            author['id'] = id
            author_data.append(author)
        
        if not author_data:            
            author_data = [{'name':[a]} for a in data['metadata'].get('author', [])]

        dai_list = []
        for author in author_data:
            unique_id = data['record']['id'] + '_' + author.get('id', author['name'][0])
            unique_id = unique_id.replace(':', '')
            name = MODS.name(
                MODS.displayForm(author['name'][0]),
                type='personal',
                id=unique_id
                )
            surname = author.get('surname')
            if surname:
                name.append(MODS.namePart(surname[0], type="family"))
            firstname = author.get('firstname')
            if firstname:
                name.append(MODS.namePart(firstname[0], type="given"))
                
            name.append(                    
                     MODS.role(
                       MODS.roleTerm('aut',
                                     type='code',
                                     authority='marcrelator')
                       ))
            mods.append(name)
            dai = author.get('dai')
            if dai:
                dai_list.append((unique_id, dai))

        if dai_list:
            daiList = DAI.daiList()
            for id, dai in dai_list:
                daiList.append(DAI.identifier(dai[0], IDRef=id, authority='info:eu-repo/dai/nl'))
                
            mods.append(MODS.extension(daiList))

    
        titleInfo = MODS.titleInfo(
            MODS.title(data['metadata'].get('title', [])[0])
            )
        titleInfo.attrib['{%s}lang' % self.ns['xml']] = data['metadata'].get(
            'language', ['en'])[0]
        mods.append(titleInfo)
        
        mods.attrib['{%s}schemaLocation' % XSI_NS] = self.schemas['mods']
        
        element.append(mods)

        
class DIDL(MataDataPrefix):
    
    name('dare_didl')
    
    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'didl': "urn:mpeg:mpeg21:2002:02-DIDL-NS",
                   'dii': "urn:mpeg:mpeg21:2002:01-DII-NS",
                   'dip': "urn:mpeg:mpeg21:2002:01-DIP-NS",
                   'dcterms': "http://purl.org/dc/terms/",
                   'xsi': "http://www.w3.org/2001/XMLSchema-instance",
                   'dc': 'http://purl.org/dc/elements/1.1/',
                   }

        self.schemas = {'didl': 'urn:mpeg:mpeg21:2002:02-DIDL-NS http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/did/didl.xsd urn:mpeg:mpeg21:2002:01-DII-NS http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/dii/dii.xsd urn:mpeg:mpeg21:2005:01-DIP-NS http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/dip/dip.xsd'}
        
    def __call__(self, element, metadata):
        data = metadata.record
        
        DIDL = ElementMaker(namespace=self.ns['didl'], nsmap=self.ns)
        DII = ElementMaker(namespace=self.ns['dii'])
        DIP = ElementMaker(namespace=self.ns['dip'])
        DCTERMS = ElementMaker(namespace=self.ns['dcterms'])

        oai_url = self.config.url+'?verb=GetRecord&metadataPrefix=dare_didl&identifier=%s' % (
            self.config.get_oai_id(data['record']['id']))

        # generate oai_dc for this feed
        oai_dc_data = DIDL.Resource(mimetype="application/xml")
        OAIDC('oai_dc', self.config, self.db)(oai_dc_data, metadata)
        # generate mods for this feed
        mods_data = DIDL.Resource(mimetype="application/xml")
        MODS('mods', self.config, self.db)(mods_data, metadata)

        asset_data = []
        
        didl = DIDL.DIDL(
            DIDL.Item(
             DIDL.Descriptor(
              DIDL.Statement(
               DII.Identifier(data['metadata'].get('dare_id', [''])[0]),
              mimeType="application/xml")
              ),
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
              DIDL.Component(oai_dc_data)
              ),
             DIDL.Item(
              DIDL.Descriptor(
               DIDL.Statement(
                DIP.ObjectType('info:eu-repo/semantics/descriptiveMetadata'),
                mimeType="application/xml")
               ),
              DIDL.Component(mods_data)
              ),
             DIDL.Item(
              DIDL.Descriptor(
               DIDL.Statement(
                DIP.ObjectType('info:eu-repo/semantics/humasStartPage'),
                mimeType="application/xml")
                ),
              DIDL.Component(
               DIDL.Resource(mimetype="text/html", ref=data['metadata'].get('url', [''])[0])
               )
              ),
             )
            )

        for root_item in didl:
            for asset in data['metadata'].get('asset', []):
                item = DIDL.Item(
                    DIDL.Descriptor(
                     DIDL.Statement(
                      DIP.ObjectType('info:eu-repo/semantics/humasStartPage'),
                      mimeType="application/xml")
                     ),
                    DIDL.Component(
                     DIDL.Resource(mimetype=asset['mimetype'],
                                   ref=asset['url'])
                     )
                    )
                root_item.append(item)
            break
        
        
        didl.attrib['{%s}schemaLocation' % XSI_NS] = self.schemas['didl']
        element.append(didl)
