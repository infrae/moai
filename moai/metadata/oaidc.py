
from lxml.builder import ElementMaker

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
  
class OAIDC(object):
    """The standard OAI Dublin Core metadata format.
    
    Every OAI feed should at least provide this format.

    It is registered under the name 'oai_dc'
    """
    
    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                   'dc':'http://purl.org/dc/elements/1.1/'}
        self.schemas = {
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'}
        
    def get_namespace(self):
        return self.ns[self.prefix]

    def get_schema_location(self):
        return self.schemas[self.prefix]
    
    def __call__(self, element, metadata):

        data = metadata.record
        
        OAI_DC =  ElementMaker(namespace=self.ns['oai_dc'],
                               nsmap =self.ns)
        DC = ElementMaker(namespace=self.ns['dc'])

        oai_dc = OAI_DC.dc()
        oai_dc.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
            self.ns['oai_dc'],
            self.schemas['oai_dc'])

        for field in ['title', 'creator', 'subject', 'description',
                      'publisher', 'contributor', 'type', 'format',
                      'identifier', 'source', 'language', 'date',
                      'relation', 'coverage', 'rights']:
            el = getattr(DC, field)
            for value in data['metadata'].get(field, []):
                if field == 'identifier' and data['metadata'].get('url'):
                    value = data['metadata']['url'][0]
                oai_dc.append(el(value))
        
        element.append(oai_dc)
