import datetime

from zope.interface import implements

from moai.interfaces import IContentObject, IContentSet

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

