import os
import time
import datetime

from lxml import etree

from moai import ConfigurationProfile, name
from moai.content import XMLContentObject
from moai.update import DatabaseUpdater
from moai.database.btree import BTreeDatabase
from moai.provider.file import FileBasedContentProvider
from moai.server import Server, ServerConfig

class ExampleContentObject(XMLContentObject):

    def add_data(self, path):
        self.nsmap = {'ex':'http://example.org'}
        doc = etree.parse(path)
        self.root = doc.getroot()

        self.id = self.xpath('ex:id/text()', 'id', unicode, required=True)
        self.content_type = self.root.xpath('local-name()')
        if self.content_type == 'publication':
            self.label = self.xpath('ex:title/text()', 'title', unicode, required=True)
        else:
            self.label = self.xpath('ex:name/text()', 'title', unicode, required=True)
            
        self.when_modified = datetime.datetime(*time.gmtime(os.path.getmtime(path))[:6])
        self.deleted = False
        self.sets = self.xpath('ex:set/@ref', 'set', unicode, required=False, multi=True)
        self.is_set = self.content_type == 'set'
        self._fields = {
            'abstract': [self.xpath('ex:abstract', 'abstract', unicode, required=False)],
            'author': self.xpath('ex:author/@ref', 'author', unicode, required=False, multi=True)
            }
        
class ExampleConfiguration(ConfigurationProfile):
    name('example')
    
    def get_content_provider(self):
        path = os.path.join(os.path.dirname(__file__),'example_data')
        provider = FileBasedContentProvider(path, '*.xml')
        provider.set_logger(self.log)
        provider.set_content_class(ExampleContentObject)
        return provider


    def get_database_updater(self):
        return DatabaseUpdater(self.get_content_provider(),
                               BTreeDatabase('/tmp/moai', 'w'),
                               self.log)

    def get_database(self):
        return BTreeDatabase('/tmp/moai', 'r')
    
    def get_server(self):
        server = Server('http://localhost:8080/repo',
                        self.get_database())
        server.add_config(
            ServerConfig('example',
                         'An example OAI Server',
                         'http://localhost:8080/repo/example',
                         self.log))
        return server
                   
    def get_request():
        pass

    def start_server(log):
        start_cherrypy_server(host, port, threads, self)

        
