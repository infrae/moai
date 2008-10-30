
from zope.interface import implements

from moai.interfaces import IDatabaseUpdater
from moai.error import ContentError, DatabaseError

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
        self._log = log

    def update(self, validate=True):
        total = self.content.count()
        self._log.info('Updating %s with %s objects from %s' % (self.db.__class__.__name__,
                                                           total,
                                                           self.content.__class__.__name__))
        count = 0
        errors = 0
        for content in self.content.get_content():
            count += 1
            
            if isinstance(content, ContentError):
                errors += 1
                yield count, total, None, content
                continue

            if content.is_set:
                try:
                    self.db.add_set(content.id, content.label, content.get_values('description'))
                except Exception:
                    yield count, total, content.id, DatabaseError(content.id, 'set')
                    continue
                yield count, total, content.id, None
                continue
            
            id = content.id
            sets = content.sets
            record_data = {'id':content.id,
                           'content_type': content.content_type,
                           'when_modified': content.when_modified,
                           'deleted': content.deleted}

            metadata = {}
            got_error = False
            for name in content.field_names():
                try:
                    metadata[name] = content.get_values(name)
                except Exception:
                    yield count, total, content.id, DatabaseError(content.id, 'set')
                    got_error = True
                    break
            if got_error:
                continue

            assets = {}
            try:
                self.db.add_content(id, sets, record_data, metadata, assets)
            except Exception:
                yield count, total, content.id, DatabaseError(content.id, 'set')
                continue
            
            yield count, total, content.id, None
