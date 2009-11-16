
from lxml.builder import ElementMaker

from moai import MetaDataFormat, name
from moai.metadata import XSI_NS
from moai.extensions.didl import DIDL
        
class DareDIDL(DIDL):
    """A metadata prefix implementing the DARE DIDL metadata format
    this format is registered under the name "didl"
    Note that this format re-uses oai_dc and mods formats that come with
    MOAI by default
    """    
    name('nl_didl')

    def __init__(self, prefix, config, db):
        super(DareDIDL, self).__init__(prefix, config, db)
        self.prefix = 'nl_didl'

        self.ns['nl_didl'] = self.ns['didl']
        self.schemas['nl_didl'] = self.schemas['didl']

    def __call__(self, element, metadata):
        super(DareDIDL, self).__call__(element, metadata)
        data = metadata.record

        DIDL = ElementMaker(namespace=self.ns['didl'], nsmap=self.ns)
        DII = ElementMaker(namespace=self.ns['dii'])
        DIP = ElementMaker(namespace=self.ns['dip'])
        
        didl_item = element.getchildren()[0].getchildren()[0]

        didl_item.insert(0, 
           DIDL.Descriptor(
            DIDL.Statement(
            DII.Identifier(data['metadata'].get('dare_id', [''])[0]),
            mimeType="application/xml")
            ))
