
from lxml.builder import ElementMaker

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
        self.schemas = {'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'}
        
    def __call__(self, element, metadata):

        data = metadata.record
        
        OAI_DC =  ElementMaker(namespace=self.ns['oai_dc'],
                               nsmap =self.ns)
        DC = ElementMaker(namespace=self.ns['dc'])

        oai_dc = OAI_DC.dc()
        oai_dc.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (self.ns['oai_dc'],
                                                                  self.schemas['oai_dc'])

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
           'mods': 'http://www.loc.gov/standards/mods/v3/mods-3-2.xsd'}
        
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
        
        mods.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (self.ns['mods'],
                                                                self.schemas['mods'])
        
        element.append(mods)

