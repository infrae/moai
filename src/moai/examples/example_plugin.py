
from moai import Plugin, name

class ExamplePlugin(Plugin):
    name('example_plugin')

    def __init__(self, database, log, config):
        self.db = database
        self.log = log
        self.config = config
        
    def run(self, updated_ids):
        self.log.info('Hello %s from ExamplePlugin' % self.config['hello'])
        
        print 'Hello %s from example plugin -> Updating %s records' % (
                self.config['hello'], len(updated_ids))
