import os

from moai import ConfigurationProfile, name
from moai.update import DatabaseUpdater
from moai.database.btree import BTreeDatabase
from moai.provider.file import FileBasedContentProvider
from moai.server import Server, FeedConfig
from moai.http.cherry import start_server

from moai.examples.example_content import ExampleContentObject
            
class ExampleConfiguration(ConfigurationProfile):
    name('example')
    
    def get_content_provider(self):
        path = os.path.join(os.path.dirname(__file__),'example_data')
        provider = FileBasedContentProvider(path, '*.xml')
        provider.set_logger(self.log)
        return provider


    def get_database_updater(self):
        return DatabaseUpdater(self.get_content_provider(),
                               ExampleContentObject,
                               BTreeDatabase('/tmp/moai', 'w'),
                               self.log)

    def get_database(self):
        return BTreeDatabase('/tmp/moai', 'r')
    
    def get_server(self):
        server = Server('http://localhost:8080/repo',
                        self.get_database())
        server.add_config(
            FeedConfig('example',
                       'An example OAI Server',
                       'http://localhost:8080/repo/example',
                       self.log,
                       sets_allowed=['public'],
                       metadata_prefixes=['oai_dc', 'mods', 'didl']))
        return server
                   
    def start_server(self):
        start_server('127.0.0.1', 8080, 10, 'repo', self.get_server())

        
