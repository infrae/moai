
from lxml.builder import ElementMaker
from lxml.etree import SubElement

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

def get_writer(prefix, config, db):
    writers = {
        'oai_dc': OAIDCWriter
        }
    return writers[prefix](prefix, config, db)


class OAIDCWriter(object):
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
        oai_dc.attrib['{%s}schemaLocation' % XSI_NS] = self.schemas['oai_dc']

        for field in ['title', 'creator', 'subject', 'description', 'publisher',
                      'contributor', 'date', 'type', 'format', 'identifier',
                      'source', 'language', 'relation', 'coverage', 'rights']:
            el = getattr(DC, field)
            for value in data['metadata'].get(field, []):
                oai_dc.append(el(value))
        
        element.append(oai_dc)
