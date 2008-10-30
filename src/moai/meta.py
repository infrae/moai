
import martian
import logging

from moai import ConfigurationProfile, MataDataPrefix, name
import moai.core

CONFIGURATION_PROFILES={}
METADATA_PREFIXES={}

class ConfigurationProfileGrokker(martian.ClassGrokker):
    
    martian.component(ConfigurationProfile)
    martian.directive(name)
    
    def execute(self, class_, name, **kw):
        logging.getLogger('moai').info('Added configuration profile "%s"' % name)
        CONFIGURATION_PROFILES[name]=class_
        return True

class MetaDataPrefixGrokker(martian.ClassGrokker):
    
    martian.component(MataDataPrefix)
    martian.directive(name)
    
    def execute(self, class_, name, **kw):
        logging.getLogger('moai').info('Added metadata prefix "%s"' % name)
        METADATA_PREFIXES[name]=class_
        return True
    
