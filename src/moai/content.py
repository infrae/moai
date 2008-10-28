import datetime

from zope.interface import implements

from moai.interfaces import IContentProvider, IContentObject, IContentSet

class ListBasedContentProvider(object):
    implements(IContentProvider)

    def __init__(self, content, sets):
        self._content = content
        self._sets = sets

    def update(self, from_date):
        return []

    def count(self):
        return len(self._content)

    def get_content(self):
        return [DictBasedContentObject(c.copy(), self) for c in self._content]

    def get_content_by_id(self, id):
        result = [d for d in self._content if d['id'] == id]
        if result:
            return DictBasedContentObject(result[0].copy(), self)

    def get_sets(self):
        return [DictBasedContentSet(s.copy(), self) for s in self._sets]

    def get_set_by_id(self, id):
        result = [s for s in self._sets if s['id'] == id]
        if result:
            return DictBasedContentSet(result[0].copy(), self)

class DictBasedContentObject(object):
    implements(IContentObject)

    def __init__(self, data, provider):
        
        self.id = data.pop('id')
        assert (isinstance(self.id, unicode), 'id should be a unicode value')
        
        self.content_type = data.pop('content_type')
        assert (isinstance(self.content_type, unicode),
                          'content_type should be a unicode value')
        
        self.when_modified = data.pop('when_modified')
        assert (isinstance(self.when_modified, datetime.datetime),
                'when_modified should be a datetime object')
    
        
        self.deleted = data.pop('deleted')
        assert (isinstance(self.deleted, bool),
                 'when_modified should be a datetime object')
        
        self.sets = data.pop('sets')
        assert (isinstance(self.sets, list),
                'sets should be a list object')

        self.scope = data.pop('scope')
        
        self.provider = provider

        self._fields = data

    def field_names(self):
        return self._fields.keys()

    def get_values(self, field_name):
        result = self._fields[field_name]
        assert isinstance(result, list)
        return result
    
    def relation_names(self):
        return []

    def get_relations(relation_name):
        return []

class DictBasedContentSet(object):
    implements(IContentObject)

    def __init__(self, data, provider):
        
        self.id = data.pop('id')
        assert isinstance(self.id, unicode), 'id should be a unicode value'
        
        self.name = data.pop('name')
        assert isinstance(self.name, unicode), 'name should be a unicode value'
        
        self.description = data.get('description')
        assert ((None or isinstance(self.description, unicode)),
                'description should be a unicode value or None')

class DatabaseUpdater(object):

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
