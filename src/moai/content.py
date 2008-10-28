import time
import datetime
import bsddb

from zope.interface import implements

from moai.interfaces import IContentProvider, IContentObject, IContentSet, IDatabase

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

class BTreeDatabase(object):
    implements(IDatabase)

    def __init__(self, dbpath=None):

        if dbpath is None:
            self._content = bsddb.hashopen(dbpath, 'w')
            self._sets = bsddb.hashopen(dbpath, 'w')
            self._dates = bsddb.btopen(dbpath, 'w')
        else:
            self._content = bsddb.hashopen(dbpath + '_content.db', 'w')
            self._sets = bsddb.hashopen(dbpath + '_sets.db', 'w')
            self._dates = bsddb.btopen(dbpath + '_dates.db','w')

    def _datetime2key(self, datetime):
        return '%0.10d' % time.mktime(datetime.timetuple())

    def _key2datetime(self, key):
        return datetime.datetime(*time.gmtime(int(key))[:6])

    def get_record(self, id):
        return eval(self._content[id.encode('utf8')])['record']
                
    def get_metadata(self, id):
        return eval(self._content[id.encode('utf8')])['metadata']

    def get_assets(self, id):
        return eval(self_content[id.encode('utf8')])['assets']

    def get_set(self, id):
        return eval(self._sets[id.encode('utf8')])

    def remove_content(self, id):
        id = id.encode('utf8')
        data = eval(self._content.get(id))
        if data is None:
            return False
        datestamp = self._datetime2key(data['record']['when_modified'])
        del self._dates[datestamp]
        sets = eval(self._content[id])['sets']
        del self._content[id]
        for set in sets:
            set = set.encode('utf8')
            self._sets[set] = unicode(eval(self._sets[set])['content'].remove(id))
        return True
    
    def add_content(self, id, sets, record_data, meta_data, assets_data):
        datestamp =  self._datetime2key(record_data['when_modified'])
        id = id.encode('utf8')
        self._dates[datestamp]=id
        self._content[id]= unicode({'record':record_data,
                                    'metadata':meta_data,
                                    'assets':assets_data,
                                    'sets':sets})
        for set in sets:
            set = set.encode('utf8')
            if not self._sets.has_key(set):
                self._sets[set] = unicode({'content':[]})
            data = eval(self._sets[set])
            data['content'].append(id)
            self._sets[set] = unicode(data)
        return True

    def add_set(self, id, name, description):
        id = id.encode('utf8')
        if not self._sets.has_key(id):
            self._sets[id] = unicode({'content':[]})
        data = eval(self._sets[id.encode('utf8')])
        data['id'] = id
        data['name'] = name
        data['description'] = description
        self._sets[id.encode('utf8')] = unicode(data)

    def remove_set(self, id):
        data = eval(self._sets[id.encode('utf8')])
        del self._sets[id.encode('utf8')]
        for cid in data['content']:
            cid = cid.encode('utf8')
            self._content[cid] = eval(self._content[cid])['sets'].remove(id)

    def oai_sets(self, offset=0, batch_size=20):
        ids = self._sets.keys()[offset:offset+batch_size]
        for id in ids:
            result = eval(self._sets[id]).copy()
            del result['content']
            yield result

    def oai_query(self,
                  offset=0,
                  batch_size=20,
                  sets=[],
                  not_sets=[],
                  filter_sets=[],
                  from_date=None,
                  until_date=None):

        if len(self._dates) == 0:
            yield
            return

        # make sure until date is set, and not in future
        if until_date == None or until_date > datetime.datetime.now():
            until_date = datetime.datetime.now()

        # make sure from date is set
        if from_date == None:
            from_date = self._key2datetime(self._dates.first()[0])

        until_date = self._datetime2key(until_date)
        from_date = self._datetime2key(from_date)

        if from_date < self._dates.first()[0]:
            start_date = self._dates.first()[0]
        else:
             start_date = from_date

        if until_date > self._dates.last()[0]:
            stop_date = self._dates.last()[0]
        else:
            stop_date = until_date

        ids = set()
        
        # filter dates

        if start_date > self._dates.last()[0]:
            date = start_date
        else:
            date, id = self._dates.set_location(start_date)
        while date <= stop_date:
            ids.add(id)
            try:
                date, id = self._dates.next()
            except:
                break

        # filter sets

        set_ids = set()
        for set_id in sets:
            set_ids = set_ids.union(set(eval(self._sets[set_id])['content']))
        if set_ids:
            ids = ids.intersection(set_ids)

        # filter not_sets
        
        not_set_ids = set()
        for set_id in not_sets:
            not_set_ids = not_set_ids.union(set(eval(self._sets[set_id])['content']))
        if not_set_ids:
            ids = ids.difference(not_set_ids)

        # extra filter sets
        
        filter_set_ids = set()
        for set_id in filter_sets:
            filter_set_ids = filter_set_ids.union(set(eval(self._sets[set_id])['content']))
        if filter_set_ids:
            ids = ids.difference(filter_set_ids)
        
        # filter batching
        
        if batch_size < 0:
            batch_size = 0
            
        ids = list(ids)[offset:offset+batch_size]

        for id in ids:
            yield eval(self._content[id])
    
