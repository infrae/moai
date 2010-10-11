import sys
import os
import logging

import martian

import moai.meta
import moai.metadata

__version__ = '0.3.0'


def get_metadata_format(prefix):
    return moai.meta.METADATA_FORMATS.get(prefix)
    
class MOAI(object):
    def __init__(self, log, verbose=False, debug=False):
        self.verbose = verbose
        self.debug = debug
        self.log = self.setup_log(log)
        self.registry = martian.GrokkerRegistry()
        self.registry.grok('moai.meta', moai.meta)
        self.registry.grok('moai.metadata', moai.metadata)
        self._module_paths = []
        
    def get_configuration(self, config_name):
        return moai.meta.CONFIGURATION_PROFILES.get(config_name)

    def get_plugin(self, plugin_name):
        return moai.meta.PLUGINS.get(plugin_name)
    
    def get_plugin_names(self):
        return moai.meta.PLUGINS.keys()

    def add_extension_module(self, module_name):
        fromlist = []
        if '.' in module_name:
            fromlist = module_name.split('.')[:-1]
        try:
            globals = {}
            locals = {}
            module = __import__(module_name, globals, locals, fromlist)
        except ImportError, err:
            self.log.warning('Could not import extension module "%s":\n         %s' % (
                module_name, err))
            if self.debug:
                raise
            return
        self.log.info('Imported extension_module "%s"' % module_name)
        self.registry.grok(module_name, module)
        if module.__file__ not in self._module_paths:
            self._module_paths.append(module.__file__)
            if os.path.basename(module.__file__).startswith('__init__.py'):
                module_dir = os.path.dirname(module.__file__)
                for file in os.listdir(module_dir):
                    if not file.endswith('.py'):
                        continue
                    if file == '__init__.py' or file[0] in ['.', '#']:
                        continue

                    self.add_extension_module(module_name + '.%s' % file.split('.')[0])
        
    def setup_log(self, log):
        if self.verbose:
            errlog = logging.StreamHandler(sys.stderr)
            errlog.setLevel(logging.INFO)
            fmt = logging.Formatter(
                '%(levelname)-8s %(message)s', None)
            errlog.setFormatter(fmt)
            log.addHandler(errlog)
            log.setLevel(logging.INFO)
        return log
                
