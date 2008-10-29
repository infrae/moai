
from zope.interface import implements

from moai.interfaces import IDatabaseUpdater


class DatabaseUpdater(object):

    implements(IDatabaseUpdater)

    def __init__(self, content, database, log):
        self.set_database(database)
        self.set_content_provider(content)
        self.set_logger(log)

    def set_database(self, database):
        self.db = database

    def set_content_provider(self, content_provider):
        self.content = content_provider

    def set_logger(self, log):
        self.logger = log

    def update(self, validate=True):
        for content in self.content.get_content():
            id = content.id
            sets = content.sets
            record_data = {'id':content.id,
                           'content_type': content.content_type,
                           'when_modified': content.when_modified,
                           'deleted': content.deleted,
                           'scope': content.scope}
            metadata = {}
            for name in content.field_names():
                metadata[name] = content.get_values(name)

            assets = {}
            self.db.add_content(id, sets, record_data, metadata, assets)

        for set in self.content.get_sets():
            self.db.add_set(set.id, set.name, set.description)
            
        return True
