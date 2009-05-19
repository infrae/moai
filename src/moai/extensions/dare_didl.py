
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
    def __call__(self, element, metadata):
        super(DareDIDL, self).__call__(element, metadata)
