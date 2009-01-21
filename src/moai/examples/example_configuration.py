import os

from moai import ConfigurationProfile, name
from moai.update import DatabaseUpdater
from moai.database.btree import BTreeDatabase
from moai.provider.file import FileBasedContentProvider
from moai.server import Server, FeedConfig
from moai.http.cherry import start_server

from moai.examples.example_content import ExampleContentObject
            
class ExampleConfiguration(ConfigurationProfile):
    name('example_configuration')
    
    def get_content_provider(self):
        provider = FileBasedContentProvider(self.config['path'], '*.xml')
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
        server_url = 'http://localhost:%s/repo' % self.config['port']
        server = Server(server_url,
                        self.get_database())
        server.add_config(
            FeedConfig('example',
                       'An example OAI Server',
                       '%s/example' % server_url,
                       self.log,
                       sets_allowed=['public'],
                       metadata_prefixes=['oai_dc', 'mods', 'didl']))
        return server
                   
    def start_server(self):
        start_server('127.0.0.1', self.config['port'], 10, 'repo', self.get_server())

        
