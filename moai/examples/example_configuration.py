import os
import shutil

from moai import ConfigurationProfile, name
from moai.update import DatabaseUpdater
from moai.provider.file import FileBasedContentProvider
from moai.server import Server, FeedConfig
from moai.http.cherry import start_server
from moai.database.sqlite import SQLiteDatabase
from moai.examples.example_content import ExampleContentObject
            
class ExampleConfiguration(ConfigurationProfile):
    name('example_configuration')
    
    def get_content_provider(self):
        provider = FileBasedContentProvider(self.config['path'], '*.xml')
        provider.set_logger(self.log)
        return provider


    def get_database_updater(self):

        dbpath = '/tmp/moai.new.db'
        if os.path.isfile(dbpath):
            self.log.warning('removing old moai.new.db')
            os.remove(dbpath)
        
        return DatabaseUpdater(self.get_content_provider(),
                               ExampleContentObject,
                               SQLiteDatabase(dbpath, 'w'),
                               self.log)

    def get_database(self):
        if os.path.isfile('/tmp/moai.new.db'):
            shutil.move('/tmp/moai.new.db',
                        '/tmp/moai.db')
            
        return SQLiteDatabase('/tmp/moai.db', 'r')
    
    def get_server(self):
        server_url = 'http://%s:%s/repo' % (self.config['host'],
                                            self.config['port'])
        asset_path = os.path.join(os.path.dirname(__file__),
                                  'example_data',
                                  'assets')
                                  
        server = Server(server_url,
                        self.get_database())
        server.add_config(
            FeedConfig('example',
                       'An example OAI Server',
                       '%s/example' % server_url,
                       self.log,
                       base_asset_path=asset_path,
                       sets_allowed=['public'],
                       metadata_prefixes=['oai_dc', 'mods',
                                          'didl', 'nl_didl']))
        return server
                   
    def start_development_server(self):
        start_server('127.0.0.1', self.config['port'], 10, 'repo', self.get_server())

        
