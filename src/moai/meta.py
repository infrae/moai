
import martian
import logging

from moai import (ConfigurationProfile,
                  MetaDataFormat,
                  Plugin,
                  name)

CONFIGURATION_PROFILES={}
METADATA_FORMATS={}
PLUGINS={}

class ConfigurationProfileGrokker(martian.ClassGrokker):
    
    martian.component(ConfigurationProfile)
    martian.directive(name)
    
    def execute(self, class_, name, **kw):
        logging.getLogger('moai').info('Added configuration profile "%s"' % name)
        CONFIGURATION_PROFILES[name]=class_
        return True

class MetaDataFormatGrokker(martian.ClassGrokker):
    
    martian.component(MetaDataFormat)
    martian.directive(name)
    
    def execute(self, class_, name, **kw):
        logging.getLogger('moai').info('Added metadata prefix "%s"' % name)
        METADATA_FORMATS[name]=class_
        return True
    
class PluginGrokker(martian.ClassGrokker):
    
    martian.component(Plugin)
    martian.directive(name)
    
    def execute(self, class_, name, **kw):
        logging.getLogger('moai').info('Added plugin "%s"' % name)
        PLUGINS[name]=class_
        return True
