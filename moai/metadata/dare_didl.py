
from lxml.builder import ElementMaker

from moai.metadata.didl import DIDL


class DareDIDL(DIDL):
    """A metadata prefix implementing the DARE DIDL metadata format
    this format is registered under the name "didl"
    Note that this format re-uses oai_dc and mods formats that come with
    MOAI by default
    """

    def __init__(self, prefix, config, db):
        super(DareDIDL, self).__init__(prefix, config, db)
        self.prefix = 'didl'

    def __call__(self, element, metadata):
        super(DareDIDL, self).__call__(element, metadata)
        data = metadata.record

        DIDL = ElementMaker(namespace=self.ns['didl'], nsmap=self.ns)
        DII = ElementMaker(namespace=self.ns['dii'])

        didl_item = element.getchildren()[0].getchildren()[0]

        didl_item.insert(0,
                         DIDL.Descriptor(
                             DIDL.Statement(
                                 DII.Identifier(data['metadata'].get('dare_id', [''])[0]),
                                 mimeType="application/xml")
                         ))
